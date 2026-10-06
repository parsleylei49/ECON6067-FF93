"""Reconstruct modern FF3 factors from restricted CRSP/Compustat inputs.

All returns stored as decimals. No raw stock/accounting rows are exported.
Baseline: modern book equity (no deferred tax add-back after 1992), independent
NYSE sorts, positive BE, >=2 distinct observed accounting years. Memberships
fixed July–June; weights are June ME grown by lagged ex-distribution returns.
"""
from pathlib import Path
import argparse
import io
import json
import os
import hashlib
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FACTORS=['MKT_RF','SMB','HML']
CELLS=['SL','SN','SH','BL','BN','BH']

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load_factors(path):
    lines=path.read_text().splitlines()
    monthly=[x for x in lines if len(x.split(',')[0].strip())==6 and x.split(',')[0].strip().isdigit()]
    f=pd.read_csv(io.StringIO('\n'.join(monthly)),header=None,
                  names=['YYYYMM','MKT_RF','SMB','HML','RF'])
    f['date']=pd.to_datetime(f.YYYYMM.astype(str),format='%Y%m')+pd.offsets.MonthEnd(0)
    f=f.set_index('date')[FACTORS+['RF']]/100
    require(not f.index.duplicated().any(),'Duplicate benchmark month')
    require(f.notna().all().all(),'Missing benchmark factor')
    return f

def load_stocks(path, audit):
    cols=['PERMNO','PERMCO','MthCalDt','MthRet','MthRetx','MthPrc','ShrOut',
          'MthCap','MthPrevCap','MthPrevDt','SecurityEndDt','SecInfoStartDt',
          'SecInfoEndDt','PrimaryExch','SecurityType','SecuritySubType','ShareType',
          'IssuerType','USIncFlg','ConditionalType','TradingStatusFlg','MthDelFlg','vwretd']
    d=pd.concat(pd.read_csv(path,usecols=cols,chunksize=200000,low_memory=False),ignore_index=True)
    audit['raw_stock_rows']=len(d)
    # Event expansion can repeat identical observations; retain all classification
    # alternatives until resolving their effective dates.
    d=d.drop_duplicates()
    audit['stock_rows_after_exact_selected_dedup']=len(d)
    for c in ['MthCalDt','MthPrevDt','SecurityEndDt','SecInfoStartDt','SecInfoEndDt']:
        d[c]=pd.to_datetime(d[c],errors='coerce')
    d=d.rename(columns={'MthCalDt':'date','MthRet':'ret','MthRetx':'retx'})
    # A delisted security's last valid classification can end before month-end.
    asof=d[['date','SecurityEndDt']].min(axis=1)
    valid=asof.between(d.SecInfoStartDt,d.SecInfoEndDt)
    audit['rows_without_valid_security_interval']=int((~valid).sum())
    d=d[valid].copy()
    # CRSP dates can be the last trading day; join all monthly series by month.
    d['date']=d.date+pd.offsets.MonthEnd(0)
    require(not d.duplicated(['PERMNO','date']).any(),'Unresolved security/month overlap')
    eligible=(d.SecurityType.eq('EQTY') & d.SecuritySubType.eq('COM') &
              d.ShareType.eq('NS') & d.IssuerType.isin(['CORP','ACOR']) &
              d.USIncFlg.eq('Y') & d.PrimaryExch.isin(['N','A','Q']) &
              d.ConditionalType.eq('RW') & d.TradingStatusFlg.eq('A'))
    d=d[eligible].copy()
    audit['eligible_security_months']=len(d)
    audit['eligible_delisting_months']=int(d.MthDelFlg.ne('N').sum())
    audit['eligible_missing_returns']=int(d.ret.isna().sum())
    require(not d.ret.lt(-1).any(),'Total return below -100%')
    # Price*shares is thousands USD; Compustat is millions USD.
    d['me']=d.MthPrc.abs()*d.ShrOut/1000
    audit['median_me_relative_to_reported_cap']=float((d.me/(d.MthCap/1000)).median())
    d=d.sort_values(['PERMNO','date'])
    month=d.date.dt.year*12+d.date.dt.month
    prev_month=d.groupby('PERMNO').date.shift().dt.year*12+d.groupby('PERMNO').date.shift().dt.month
    d['lag_me']=d.groupby('PERMNO').me.shift().where(month.sub(prev_month).eq(1))
    # At the left boundary only, the file explicitly supplies previous cap/date.
    prev_key=d.MthPrevDt.dt.year*12+d.MthPrevDt.dt.month
    initial=d.date.eq(d.date.min()) & month.sub(prev_key).eq(1) & d.lag_me.isna()
    d.loc[initial,'lag_me']=d.loc[initial,'MthPrevCap']/1000
    audit['market_left_boundary_previous_cap_rows']=int(initial.sum())
    usable=d.ret.notna() & d.lag_me.gt(0)
    market=(d[usable].assign(wr=lambda x:x.ret*x.lag_me).groupby('date').wr.sum()/
            d[usable].groupby('date').lag_me.sum()).rename('MKT')
    market_count=d[usable].groupby('date').size().rename('market_n')
    market_ref=d.groupby('date').vwretd.first().rename('CRSP_VWRETD')
    # Conventional PERMCO consolidation: sum eligible share-class equity and
    # attach it to the largest class (PERMNO tie-break). Return is that class's.
    d['firm_me']=d.groupby(['date','PERMCO']).me.transform(lambda x:x.sum(min_count=1))
    d=d.sort_values(['date','PERMCO','me','PERMNO'],ascending=[True,True,False,True],na_position='last')
    firms=d.drop_duplicates(['date','PERMCO']).copy()
    audit['firm_months_after_share_class_consolidation']=len(firms)
    firms['me']=firms.firm_me
    firms['year']=firms.date.dt.year
    firms['month']=firms.date.dt.month
    firms['formation_year']=firms.year-(firms.month<=6).astype(int)
    return firms, market, market_count, market_ref

def load_accounts(comp_path,link_path,audit):
    c=pd.read_csv(comp_path,dtype={'gvkey':str})
    c['datadate']=pd.to_datetime(c.datadate)
    c=c[c.indfmt.eq('INDL') & c.datafmt.eq('STD') & c.consol.eq('C')].copy()
    c['year']=c.datadate.dt.year
    # Latest statement ending in each calendar year, not fyear label.
    c=c.sort_values(['gvkey','datadate']).drop_duplicates(['gvkey','year'],keep='last')
    c['history']=c.groupby('gvkey').cumcount()+1
    audit['accounting_company_years']=len(c)
    audit['non_usd_company_years']=int(c.curcd.ne('USD').sum())
    c=c[c.curcd.eq('USD')].copy()
    preferred=c.pstkrv.combine_first(c.pstkl).combine_first(c.pstk).fillna(0)
    equity=c.seq.combine_first(c.ceq+c.pstk.fillna(0)).combine_first(c['at']-c['lt'])
    c['be_modern']=equity-preferred
    c['be_original']=equity+c.txditc.fillna(0)-preferred
    audit['missing_preferred_assumed_zero']=int(c[['pstkrv','pstkl','pstk']].isna().all(axis=1).sum())
    audit['equity_fallback_rows']=int(c.seq.isna().sum())
    c['formation_year']=c.year+1
    links=pd.read_csv(link_path,dtype={'gvkey':str})
    links=links[links.LINKTYPE.isin(['LC','LU']) & links.LINKPRIM.isin(['P','C'])].copy()
    links['LINKDT']=pd.to_datetime(links.LINKDT,errors='coerce').fillna(pd.Timestamp('1900-01-01'))
    links['LINKENDDT']=pd.to_datetime(links.LINKENDDT,errors='coerce').fillna(pd.Timestamp('2099-12-31'))
    c=c.merge(links,on='gvkey',how='inner')
    c['formation_date']=pd.to_datetime(c.formation_year.astype(str)+'-06-30')
    c=c[c.formation_date.between(c.LINKDT,c.LINKENDDT)].copy()
    c=c.rename(columns={'LPERMNO':'PERMNO'})
    c['prim_rank']=c.LINKPRIM.map({'P':0,'C':1})
    c['type_rank']=c.LINKTYPE.map({'LC':0,'LU':1})
    c=c.sort_values(['PERMNO','formation_year','prim_rank','type_rank','datadate','gvkey'],
                    ascending=[True,True,True,True,False,True])
    audit['duplicate_linked_security_year_candidates']=int(c.duplicated(['PERMNO','formation_year']).sum())
    c=c.drop_duplicates(['PERMNO','formation_year'])
    require((c.datadate<c.formation_date).all(),'Accounting look-ahead')
    return c[['PERMNO','formation_year','datadate','history','be_modern','be_original']]

def formation_sample(firms,accounts,be,history):
    dec=firms[firms.month.eq(12)][['PERMNO','year','me']].copy()
    dec['formation_year']=dec.year+1
    dec=dec.rename(columns={'me':'dec_me'}).drop(columns='year')
    june=firms[firms.month.eq(6)][['PERMNO','PERMCO','year','me','PrimaryExch']].copy()
    june=june.rename(columns={'year':'formation_year','me':'june_me'})
    j=june.merge(dec,on=['PERMNO','formation_year'],validate='one_to_one')
    j=j.merge(accounts,on=['PERMNO','formation_year'],validate='one_to_one')
    j=j[j.june_me.gt(0)&j.dec_me.gt(0)&j[be].gt(0)&j.history.ge(history)].copy()
    j['bm']=j[be]/j.dec_me
    bp=[]
    for year,g in j.groupby('formation_year'):
        ny=g[g.PrimaryExch.eq('N')]
        require(len(ny)>20,f'Insufficient NYSE reference firms in {year}')
        bp.append({'formation_year':year,'size50':ny.june_me.quantile(.5),
                   'size20':ny.june_me.quantile(.2),'bm30':ny.bm.quantile(.3),
                   'bm70':ny.bm.quantile(.7),'nyse_n':len(ny)})
    bp=pd.DataFrame(bp)
    j=j.merge(bp,on='formation_year',validate='many_to_one')
    j['size']=np.where(j.june_me.le(j.size50),'S','B')
    j['value']=np.select([j.bm.le(j.bm30),j.bm.le(j.bm70)],['L','N'],default='H')
    j['cell']=j['size']+j['value']
    j['microcap']=j.june_me.le(j.size20)
    return j,bp

def portfolio_returns(firms,j,remove_micro=False):
    if remove_micro: j=j[~j.microcap].copy()
    d=firms[['PERMNO','date','formation_year','ret','retx','MthDelFlg']].merge(
        j[['PERMNO','formation_year','cell','june_me']],on=['PERMNO','formation_year'],validate='many_to_one')
    d=d.sort_values(['PERMNO','formation_year','date'])
    keys=['PERMNO','formation_year']
    # Require an unbroken July-to-current-month history. Never bridge missing
    # monthly returns or treat missing returns as zero.
    d['position']=d.groupby(keys).cumcount()+1
    d['expected']=(d.date.dt.month-7)%12+1
    d['retx_ok']=d.retx.notna() & d.retx.ge(-1)
    d['growth']=1+d.retx
    d['cumgrowth']=d.groupby(keys).growth.cumprod()
    d['laggrowth']=d.groupby(keys).cumgrowth.shift()
    d.loc[d.expected.eq(1),'laggrowth']=1.0
    d['bad_retx']=(~d.retx_ok).astype(int)
    d['prior_bad']=d.groupby(keys).bad_retx.cumsum()-d.bad_retx
    d['weight']=d.june_me*d.laggrowth
    valid=d.position.eq(d.expected)&d.prior_bad.eq(0)&d.weight.gt(0)&d.ret.notna()
    excluded=int((~valid).sum())
    d=d[valid].copy()
    d['weighted_ret']=d.weight*d.ret
    g=d.groupby(['date','cell']).agg(n=('PERMNO','size'),capital=('weight','sum'),wr=('weighted_ret','sum'),
                                    delist_n=('MthDelFlg',lambda x:x.ne('N').sum()))
    g['return']=g.wr/g.capital
    p=g['return'].unstack().reindex(columns=CELLS)
    require(p.notna().all().all(),'Empty 2x3 cell')
    fac=pd.DataFrame(index=p.index)
    fac['SMB']=p[['SL','SN','SH']].mean(axis=1)-p[['BL','BN','BH']].mean(axis=1)
    fac['HML']=p[['SH','BH']].mean(axis=1)-p[['SL','BL']].mean(axis=1)
    return fac,p,g.reset_index(),excluded

def mean_test(s):
    s=s.dropna()
    # Intercept-only Newey–West covariance, Bartlett kernel, six lags.
    # Explicit implementation avoids platform-specific SciPy binary dependencies.
    x=s.to_numpy(); n=len(x); residual=x-x.mean()
    meat=float(residual@residual)
    for lag in range(1,min(6,n-1)+1):
        meat+=2*(1-lag/7)*float(residual[lag:]@residual[:-lag])
    se=math.sqrt(max(0,meat/n**2*n/(n-1)))
    t=float(x.mean()/se) if se else float('nan')
    return {'n':len(s),'mean_monthly_pct':s.mean()*100,'vol_annual_pct':s.std(ddof=1)*np.sqrt(12)*100,
            't_HAC6':t,'p_HAC6':math.erfc(abs(t)/math.sqrt(2)),
            'ci_low_monthly_pct':float((x.mean()-1.95996398454*se)*100),
            'ci_high_monthly_pct':float((x.mean()+1.95996398454*se)*100)}

def compare(recon,official):
    rows=[]
    for factor in FACTORS:
        z=pd.concat([recon[factor].rename('a'),official[factor].rename('b')],axis=1).dropna()
        diff=z.a-z.b
        rows.append({'factor':factor,'start':str(z.index.min().date()),'end':str(z.index.max().date()),
                     'n':len(z),'correlation':z.a.corr(z.b),'mean_difference_bps':diff.mean()*10000,
                     'RMSE_bps':np.sqrt(np.mean(diff**2))*10000,
                     'annual_tracking_error_pct':diff.std(ddof=1)*np.sqrt(12)*100,
                     'max_absolute_difference_bps':diff.abs().max()*10000})
    return pd.DataFrame(rows)

def plot_all(recon,official,variants,out):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    def lines(ax,z):
        values=(1+z).cumprod()-1
        for i,col in enumerate(values):
            ax.plot(values.index,values[col],label=col,color=['#126782','#e58f29'][i],
                    linestyle=['-','--'][i],linewidth=1.6)
        ticks=[values.index.min()]+[pd.Timestamp(f'{y}-01-01') for y in [2005,2010,2015,2020] if values.index.min()<pd.Timestamp(f'{y}-01-01')<values.index.max()]+[values.index.max()]
        ax.set_xticks(ticks,[d.strftime('%Y-%m') if i in [0,len(ticks)-1] else d.strftime('%Y') for i,d in enumerate(ticks)])
        ax.set_xlim(values.index.min(),values.index.max());ax.legend();ax.grid(alpha=.15)
    fig,axes=plt.subplots(3,1,figsize=(10,10),layout='constrained')
    for ax,f in zip(axes,FACTORS):
        z=pd.concat([recon[f].rename('Reconstructed'),official[f].rename('French benchmark')],axis=1).dropna()
        lines(ax,z)
        ax.set_title(f+' | compounded factor-return index');ax.set_ylabel('Index − 1');ax.set_xlabel('')
        ax.grid(alpha=.15)
    fig.suptitle('Same start date within each factor; gross theoretical indices, not investable wealth',fontsize=11)
    fig.savefig(out/'factor_cumulative.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),layout='constrained')
    for ax,f in zip(axes,FACTORS):
        z=pd.concat([recon[f].rename('r'),official[f].rename('o')],axis=1).dropna()*100
        ax.scatter(z.o,z.r,s=9,alpha=.5,color='#126782');lo=z.min().min();hi=z.max().max()
        ax.plot([lo,hi],[lo,hi],color='#e58f29');ax.set_title(f);ax.set_xlabel('Benchmark monthly %');ax.set_ylabel('Reconstructed monthly %')
    fig.savefig(out/'factor_scatter.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(10,6.5),layout='constrained')
    for ax,f in zip(axes,['SMB','HML']):
        z=pd.concat([recon[f].rename('Baseline'),variants['ex_micro'][f].rename('Exclude microcaps')],axis=1).dropna()
        lines(ax,z);ax.set_title(f);ax.set_ylabel('Index − 1');ax.set_xlabel('')
    fig.suptitle('Microcap extension | original breakpoints fixed; no trading costs',fontsize=11)
    fig.savefig(out/'microcap_extension.png',dpi=180);plt.close(fig)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,default=Path.home()/'Downloads')
    args=parser.parse_args()
    out=ROOT/'results';out.mkdir(exist_ok=True)
    plots=ROOT/'figures';plots.mkdir(exist_ok=True)
    audit={}
    stock=args.data_root/'02_Monthly_Stocks_and_Factors/data/monthly_stock.csv'
    comp=args.data_root/'04_Supplementary_Data/data/Compustat.csv'
    link=args.data_root/'04_Supplementary_Data/data/CCM.csv'
    ff=args.data_root/'02_Monthly_Stocks_and_Factors/data/F-F factors and RF.csv'
    official=load_factors(ff)
    print('Loading and resolving stock records...',flush=True)
    firms,market,market_n,market_ref=load_stocks(stock,audit)
    print('Constructing accounting links...',flush=True)
    accounts=load_accounts(comp,link,audit)
    j,bp=formation_sample(firms,accounts,'be_modern',2)
    base,p6,counts,excluded=portfolio_returns(firms,j)
    audit['baseline_excluded_return_rows']=excluded
    audit['baseline_formation_firm_years']=len(j)
    audit['baseline_first_formation']=int(j.formation_year.min())
    audit['baseline_last_formation']=int(j.formation_year.max())
    recon=pd.concat([(market-official.RF).rename('MKT_RF'),base],axis=1).loc['2000-01-01':'2025-12-31']
    recon.index.name='date'
    benchmark=official.reindex(recon.index)
    recon.to_csv(out/'constructed_factors.csv',float_format='%.12g')
    benchmark.to_csv(out/'benchmark_factors.csv',float_format='%.12g')
    p6.to_csv(out/'six_portfolio_returns.csv',float_format='%.12g')
    counts.to_csv(out/'portfolio_month_diagnostics.csv',index=False,float_format='%.12g')
    bp.to_csv(out/'june_breakpoints.csv',index=False,float_format='%.12g')
    coverage=j.groupby('formation_year').agg(firms=('PERMNO','size'),microcaps=('microcap','sum'),june_me=('june_me','sum'))
    coverage['microcap_count_share']=coverage.microcaps/coverage.firms
    coverage['microcap_capital_share']=j[j.microcap].groupby('formation_year').june_me.sum()/coverage.june_me
    coverage.to_csv(out/'formation_coverage.csv')
    variants={}
    variants['ex_micro'],_,_,_=portfolio_returns(firms,j,True)
    jtax,_=formation_sample(firms,accounts,'be_original',2)
    variants['original_BE'],_,_,_=portfolio_returns(firms,jtax)
    jone,_=formation_sample(firms,accounts,'be_modern',1)
    variants['one_year_history'],_,_,_=portfolio_returns(firms,jone)
    for name,v in variants.items(): v.to_csv(out/(name+'_factors.csv'),float_format='%.12g')
    comp_table=compare(recon,benchmark);comp_table.to_csv(out/'benchmark_comparison.csv',index=False)
    summary=[]
    for f in FACTORS:
        valid=recon[f].dropna().index
        for name,series in [('reconstructed',recon[f]),('benchmark',benchmark[f])]:
            summary.append({'factor':f,'series':name,**mean_test(series.loc[valid])})
    pd.DataFrame(summary).to_csv(out/'summary_statistics.csv',index=False)
    extension=[]
    for f in ['SMB','HML']:
        for sample,start,end in [('full','2000','2025-12-31'),('early','2000','2013-12-31'),('late','2014','2025-12-31')]:
            z=pd.concat([base[f].rename('base'),variants['ex_micro'][f].rename('ex')],axis=1).dropna().loc[start:end]
            for name,s in [('baseline',z.base),('ex_micro',z.ex),('paired_difference',z.ex-z.base)]:
                extension.append({'factor':f,'period':sample,'series':name,**mean_test(s)})
    pd.DataFrame(extension).to_csv(out/'extension_tests.csv',index=False)
    sensitivity=[]
    for name,v in variants.items():
        for f in ['SMB','HML']:
            z=pd.concat([v[f].rename('variant'),base[f].rename('base'),benchmark[f].rename('official')],axis=1).dropna()
            sensitivity.append({'variant':name,'factor':f,'n':len(z),
                                'mean_shift_bps':(z.variant-z.base).mean()*10000,
                                'correlation_with_official':z.variant.corr(z.official),
                                'RMSE_vs_official_bps':np.sqrt(np.mean((z.variant-z.official)**2))*10000})
    pd.DataFrame(sensitivity).to_csv(out/'sensitivity_comparison.csv',index=False)
    pd.concat([market,market_ref,market_n],axis=1).to_csv(out/'market_diagnostics.csv')
    # Specific validation checks, including independent arithmetic identities.
    require(np.allclose(base.SMB,(p6.SL+p6.SN+p6.SH-p6.BL-p6.BN-p6.BH)/3),'SMB identity failed')
    require(np.allclose(base.HML,(p6.SH+p6.BH-p6.SL-p6.BL)/2),'HML identity failed')
    require(not recon.index.duplicated().any(),'Duplicate output month')
    require((counts.n>0).all(),'Empty cell')
    require(recon.index.to_period('M').equals(pd.period_range('2000-01','2025-12',freq='M')),'Output month grid')
    audit['factor_missing_months']={f:int(recon[f].isna().sum()) for f in FACTORS}
    audit['min_cell_n']=int(counts.n.min())
    audit['retained_portfolio_delisting_rows']=int(counts.delist_n.sum())
    audit['tests_passed']=['unique security-month after temporal resolution','accounting predates formation',
        'unique June linked sample','positive nonempty six-portfolio weights','SMB arithmetic identity',
        'HML arithmetic identity','312-month output grid','benchmark percent to decimal conversion']
    (out/'pipeline_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(comp_table.to_string(index=False),flush=True)
    print('Plotting...',flush=True)
    plot_all(recon,benchmark,variants,plots)
    print(json.dumps(audit,indent=2),flush=True)

if __name__=='__main__': main()
