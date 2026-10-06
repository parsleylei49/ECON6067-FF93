# Data access and licensing

No restricted raw files are distributed with this project. Do not upload CRSP, Compustat, CCM, the course password, restricted download URLs, or the paper PDF to GitHub. Obtain the packages through your own authorized course/WRDS access. Classmates or markers without the raw files can inspect the processed monthly factors, six portfolio returns, diagnostics and all final results here, but cannot independently repeat the raw construction without licensed inputs.

The `--data-root` directory must contain:

```text
02_Monthly_Stocks_and_Factors/
  data/
    monthly_stock.csv
    F-F factors and RF.csv
04_Supplementary_Data/
  data/
    Compustat.csv
    CCM.csv
```

Use the original supplied CSV schemas. Their package README and DATA_DICTIONARY are the first references for field definitions. `results/input_audit.json` records byte sizes and SHA-256 hashes for the exact input vintage used. A hash mismatch indicates different bytes, not necessarily bad data; rerun and review differences before reusing the report's interpretation.

## Input contract

| File | Grain and key | Required fields |
| --- | --- | --- |
| monthly_stock.csv | Expanded monthly observations; resolve to PERMNO × month | PERMNO, PERMCO, MthCalDt, MthRet, MthRetx, MthPrc, ShrOut, MthCap, MthPrevCap, MthPrevDt, SecurityEndDt, SecInfoStartDt, SecInfoEndDt, PrimaryExch, SecurityType, SecuritySubType, ShareType, IssuerType, USIncFlg, ConditionalType, TradingStatusFlg, MthDelFlg, vwretd |
| Compustat.csv | gvkey × annual statement date | gvkey, datadate, indfmt, datafmt, consol, curcd, seq, ceq, pstk, at, lt, pstkrv, pstkl, txditc |
| CCM.csv | Historical firm–security link intervals | gvkey, LPERMNO, LINKTYPE, LINKPRIM, LINKDT, LINKENDDT |
| F-F factors and RF.csv | Monthly YYYYMM followed by 4 return columns | MKT−RF, SMB, HML, RF in percent; introductory/annual lines are skipped |

## Units and missing values

CRSP returns are decimal fractions. French factors are percentage units before conversion. Shares are thousands; price × shares / 1000 produces millions of USD, comparable to Compustat book equity. Do not replace return nulls with zero. Company/accounting raw intermediates are not saved; only aggregated derived research results are included.

## Why early factors are missing

The file starts in January 2000, while June formation requires prior December equity and prior calendar-year accounting. Two observed annual records first become available for June 2002. To reconstruct all of 2000–2025 with the same history proxy, request stock history including December 1998 and accounting history from at least 1997, plus appropriate links. More extensive prehistory is preferable for a meaningful seasoning rule. Never fill missing reconstructed factors with official factors.

The public benchmark documentation is available at the [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html). A newly downloaded series may have a different vintage; do not silently replace the supplied July 2026 benchmark.

Derived aggregates are included for grading/review, not as a redistribution of vendor microdata. Confirm your institution's license before public release; a private repository with teaching-team access is the conservative route.
