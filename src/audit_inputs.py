"""Audit supplied FF93 input files without changing or publishing raw data."""
from pathlib import Path
import argparse
import hashlib
import json
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=Path, default=Path.home() / 'Downloads')
    args = parser.parse_args()
    out = Path(__file__).resolve().parents[1] / 'results'
    out.mkdir(parents=True, exist_ok=True)
    stock_path = args.data_root / '02_Monthly_Stocks_and_Factors/data/monthly_stock.csv'
    cols = ['PERMNO','PERMCO','YYYYMM','MthCalDt','MthRet','MthRetx','MthCap',
            'MthPrc','ShrOut','SecInfoStartDt','SecInfoEndDt','PrimaryExch',
            'SecurityType','SecuritySubType','ShareType','IssuerType','USIncFlg',
            'ConditionalType','TradingStatusFlg','MthDelFlg']
    stock = pd.concat(pd.read_csv(stock_path, usecols=cols, chunksize=200000,
                                 low_memory=False), ignore_index=True)
    audit = {'stock_raw_rows': len(stock), 'stock_start': int(stock.YYYYMM.min()),
             'stock_end': int(stock.YYYYMM.max()),
             'stock_unique_security_months': len(stock.drop_duplicates(['PERMNO','YYYYMM']))}
    # Duplicates may be distribution-event expansion, not extra return observations.
    core = ['PERMNO','PERMCO','YYYYMM','MthRet','MthRetx','MthCap','MthPrc','ShrOut']
    audit['stock_distinct_core_records'] = len(stock[core].drop_duplicates())
    dup = stock[stock.duplicated(['PERMNO','YYYYMM'], keep=False)]
    conflicts = dup.groupby(['PERMNO','YYYYMM'])[cols[3:]].nunique(dropna=False).gt(1).sum()
    audit['duplicate_key_conflicts_by_column'] = {k:int(v) for k,v in conflicts.items()}
    for c in ['MthRet','MthRetx','MthCap']:
        audit[c+'_missing_rows'] = int(stock[c].isna().sum())
    stock = stock.drop_duplicates(cols)
    audit['rows_after_identical_selected_record_dedup'] = len(stock)
    date = pd.to_datetime(stock.MthCalDt)
    active = date.between(pd.to_datetime(stock.SecInfoStartDt),
                          pd.to_datetime(stock.SecInfoEndDt))
    audit['rows_outside_security_info_interval'] = int((~active).sum())
    mask = (stock.SecurityType.eq('EQTY') & stock.SecuritySubType.eq('COM') &
            stock.ShareType.eq('NS') & stock.IssuerType.eq('CORP') & stock.USIncFlg.eq('Y') &
            stock.PrimaryExch.isin(['N','A','Q']) & stock.ConditionalType.eq('RW') &
            stock.TradingStatusFlg.eq('A') & active)
    eligible = stock[mask]
    audit['eligible_common_stock_rows'] = len(eligible)
    audit['eligible_duplicate_security_months'] = int(eligible.duplicated(['PERMNO','YYYYMM']).sum())
    audit['eligible_return_below_minus_one'] = int(eligible.MthRet.lt(-1).sum())
    audit['eligible_delisting_months'] = int(eligible.MthDelFlg.ne('N').sum())
    ratio = eligible.MthCap / (eligible.MthPrc.abs()*eligible.ShrOut)
    audit['market_cap_to_price_times_shares_median'] = float(ratio.median())
    audit['market_cap_units'] = 'thousands USD; Compustat amounts are millions USD'
    annual = eligible.assign(year=eligible.YYYYMM//100).groupby('year').agg(
        security_months=('PERMNO','size'), securities=('PERMNO','nunique'),
        companies=('PERMCO','nunique'), missing_returns=('MthRet',lambda s:s.isna().sum()))
    annual.to_csv(out/'stock_coverage_by_year.csv')
    comp_path = args.data_root / '04_Supplementary_Data/data/Compustat.csv'
    comp = pd.read_csv(comp_path, dtype={'gvkey':str})
    audit['compustat_rows'] = len(comp)
    audit['compustat_start'] = comp.datadate.min()
    audit['compustat_end'] = comp.datadate.max()
    audit['compustat_duplicate_company_statement_dates'] = int(comp.duplicated(['gvkey','datadate']).sum())
    audit['compustat_formats'] = {c:comp[c].value_counts(dropna=False).to_dict()
                                  for c in ['indfmt','datafmt','consol','curcd','costat']}
    link_path = args.data_root / '04_Supplementary_Data/data/CCM.csv'
    link = pd.read_csv(link_path,dtype={'gvkey':str})
    audit['ccm_rows'] = len(link)
    audit['ccm_linktype'] = link.LINKTYPE.value_counts().to_dict()
    audit['ccm_linkprim'] = link.LINKPRIM.value_counts().to_dict()
    ff_path = args.data_root/'02_Monthly_Stocks_and_Factors/data/F-F factors and RF.csv'
    lines = ff_path.read_text().splitlines()
    monthly = [x for x in lines if len(x.split(',')[0].strip())==6 and x.split(',')[0].strip().isdigit()]
    audit['official_factor_months'] = len(monthly)
    audit['official_factor_start'] = monthly[0].split(',')[0]
    audit['official_factor_end'] = monthly[-1].split(',')[0]
    audit['official_factor_header'] = lines[0]
    audit['scope'] = 'Available stock/accounting data do not overlap the original July 1963–December 1991 test period.'
    audit['course_requirements_status'] = 'Verified 6 October 2026; see docs/course_requirements.md. Initial audit screens are not final pipeline sample counts.'
    hashes = {}
    for p in [stock_path, comp_path, link_path, ff_path]:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024), b''): h.update(block)
        hashes[p.name]={'bytes':p.stat().st_size,'sha256':h.hexdigest()}
    audit['input_manifest']=hashes
    (out/'input_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(audit,indent=2,ensure_ascii=False))

if __name__ == '__main__':
    main()
