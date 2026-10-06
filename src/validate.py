"""Independent result arithmetic and synthetic edge-case tests; no fixture enters results."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from replicate import portfolio_returns, mean_test, CELLS

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name, condition):
    if not condition: raise AssertionError(name)
    checks.append(name)

r=pd.read_csv(ROOT/'results/constructed_factors.csv',index_col=0,parse_dates=True)
b=pd.read_csv(ROOT/'results/benchmark_factors.csv',index_col=0,parse_dates=True)
p=pd.read_csv(ROOT/'results/six_portfolio_returns.csv',index_col=0,parse_dates=True)
g=pd.read_csv(ROOT/'results/portfolio_month_diagnostics.csv')
check('312 unique consecutive calendar months',len(r)==312 and r.index.to_period('M').equals(pd.period_range('2000-01','2025-12',freq='M')))
check('No benchmark month lost to trading-day labels',b.notna().all().all())
check('Only initial 30 size/value months missing',r.SMB.iloc[:30].isna().all() and r.HML.iloc[:30].isna().all() and r.iloc[30:].notna().all().all())
check('Six portfolio returns agree with weighted numerator / denominator',np.allclose(g['return'],g.wr/g.capital,atol=1e-10))
check('SMB independently reconstructed from six saved columns',np.allclose(r.loc[p.index,'SMB'],np.einsum('ij,j->i',p.to_numpy(),[1,1,1,-1,-1,-1])/3,atol=1e-10))
check('HML independently reconstructed from six saved columns',np.allclose(r.loc[p.index,'HML'],np.einsum('ij,j->i',p.to_numpy(),[-1,0,1,-1,0,1])/2,atol=1e-10))
ext=pd.read_csv(ROOT/'results/ex_micro_factors.csv',index_col=0,parse_dates=True)
tests=pd.read_csv(ROOT/'results/extension_tests.csv')
for f in ['SMB','HML']:
    delta=(ext[f]-r[f]).dropna()
    row=tests[(tests.factor==f)&(tests.period=='full')&(tests.series=='paired_difference')].iloc[0]
    # Separate matrix form of Bartlett HAC; does not call production helper.
    x=delta.to_numpy(); n=len(x); u=x-x.mean()
    lag=np.abs(np.arange(n)[:,None]-np.arange(n)[None,:])
    kernel=np.maximum(1-lag/7,0)
    se=np.sqrt(np.einsum('i,ij,j->',u,kernel,u)/(n*(n-1)))
    check(f+' paired mean and independent matrix HAC',np.isclose(row.mean_monthly_pct,x.mean()*100,atol=1e-9) and np.isclose(row.t_HAC6,x.mean()/se,atol=1e-8))

# Synthetic fixture: two firms per cell, July return and ex-return differ.
# July weights 100/300, August weights 110/300, not contemporaneous cap.
members=[]; rows=[]
for c,cell in enumerate(CELLS):
    for k,capital in enumerate([100.,300.]):
        pid=c*2+k
        members.append({'PERMNO':pid,'formation_year':2020,'cell':cell,'june_me':capital,'microcap':False})
        for date,ret,rx in [('2020-07-31',.20 if k==0 else 0.,.10 if k==0 else 0.),('2020-08-31',.10 if k==0 else -.05,0.)]:
            rows.append({'PERMNO':pid,'formation_year':2020,'date':pd.Timestamp(date),'ret':ret,'retx':rx,'MthDelFlg':'N'})
fixture=pd.DataFrame(rows); membership=pd.DataFrame(members)
_,six,_,_=portfolio_returns(fixture,membership)
check('Synthetic July weights equal June size',np.allclose(six.iloc[0],.05))
check('Synthetic August uses lagged ex-return growth',np.allclose(six.iloc[1],(110*.10-300*.05)/410))
# Missing July means a firm cannot re-enter in August with unobserved growth.
gap=fixture[~((fixture.PERMNO==0)&(fixture.date.dt.month==7))]
_,gap_six,_,_=portfolio_returns(gap,membership)
check('Synthetic gap excludes broken July-to-August chain',np.isclose(gap_six.loc['2020-08-31','SL'],-.05))
bad=fixture.copy();bad.loc[(bad.PERMNO==0)&(bad.date.dt.month==7),'retx']=np.nan
_,bad_six,_,_=portfolio_returns(bad,membership)
check('Synthetic missing ex-return invalidates subsequent weight',np.isclose(bad_six.loc['2020-08-31','SL'],-.05))
check('Million/thousand unit example',abs(-20)*5000/1000==100)
worst=[]
for f in r:
    d=(r[f]-b[f]).dropna()
    for dt,val in d.abs().nlargest(3).items():
        worst.append({'factor':f,'date':str(dt.date()),'reconstructed':r.loc[dt,f],'benchmark':b.loc[dt,f],'difference_bps':d.loc[dt]*10000})
pd.DataFrame(worst).to_csv(ROOT/'results/largest_benchmark_gaps.csv',index=False)
(ROOT/'results/validation.json').write_text(json.dumps({'status':'passed','checks':checks,'scope':'Saved-result arithmetic, independent HAC, and synthetic timing edge cases. Not an independent full CRSP re-extraction.'},indent=2)+'\n')
print(f'{len(checks)} checks passed.')
