# ECON6067 — Fama and French (1993) replication

Author: LEI Jinqiu, 3036762812

## Current status

Input audit completed on 6 October 2026. This is a preparation package, not a completed final-project submission. The course project URL requires a course password. The assigned replication target, extension requirements, report length, submission format, and deadline still need to be verified against that page.

## Verified input coverage

- Monthly stock data: January 2000–December 2025; 2,423,212 raw rows, 2,393,591 distinct security-month keys.
- Compustat: 301,565 rows; statement dates January 2000–December 2025; USD and CAD records present. No duplicate gvkey–statement-date keys.
- CCM: 39,761 link records, with link types LC/LU/LS and several primary-link classifications.
- Supplied official factors: July 1926–July 2026, from the July 2026 CRSP database vintage. Monthly observations are in percentage units, while CRSP returns are decimals.
- The supplied stock and accounting data do not cover the paper's July 1963–December 1991 stock-return tests. Reconstruction on a later period must be labelled a methodological replication, not numerical reproduction of the historical tables.

## Material audit findings

1. Raw duplicate security-month rows agree on return, price, shares, and market capitalization, but 1,542 duplicate keys have conflicting historical security classifications. Select the classification valid on the observation date before checking uniqueness. Simply dropping the first duplicate can assign the wrong exchange or security type.
2. After deduplicating the selected fields, 13,390 rows fall outside their attached security-information interval. They require temporal resolution/exclusion, not indiscriminate inclusion.
3. The initial universe screen (ordinary US-incorporated corporate common stock, NYSE/AMEX/NASDAQ, regular-way active trading, valid classification date) yields 1,339,347 rows and no duplicate security-month keys. This is an audited preliminary universe, not the final accounting-linked portfolio sample. Delisting return treatment still requires verification before production analysis.
4. MthCap equals absolute price times shares outstanding at the median. Shares are thousands: convert market equity to millions before forming book-to-market ratios with Compustat.
5. Inactive Compustat firms are present and must not be removed solely because their current status is inactive.
6. Raw files are restricted course inputs. They remain at the user's download location and must not be committed to a public repository.

Exact counts, input hashes, and format distributions are in `results/input_audit.json`; annual stock coverage is in `results/stock_coverage_by_year.csv`.

## Re-run the audit

Requires Python and pandas. From this project directory:

```bash
python src/audit_inputs.py --data-root /path/to/downloads
```

The data root should contain the original `02_Monthly_Stocks_and_Factors` and `04_Supplementary_Data` directories. The audit reads originals and writes only derived aggregate diagnostics under `results/`.

## Proposed analysis, pending the course brief

1. Resolve security-month duplication and historical classifications; document common-stock selection, missing returns, delistings, company-level share-class aggregation, and market-equity units.
2. Construct book equity from annual statements using the preferred-stock hierarchy, currency screens, and explicitly documented missing-value fallbacks; enforce point-in-time CCM linkage and an accounting-history screen. Data beginning in 2000 create left truncation for the history screen.
3. Each June, use prior-calendar-year book equity and December market equity, plus June size, to form independent NYSE size and book-to-market breakpoints. Hold memberships from July to June and calculate value-weighted returns with predetermined weights.
4. Build six 2×3 portfolios and SMB/HML; construct/document the market excess return separately. Compare monthly reconstructed factors with the supplied official series using correlations, mean differences, and tracking error over matched months.
5. If assigned, form 25 size–book-to-market test portfolios and compare CAPM and three-factor regressions, alphas, and fit, with stated inference assumptions.
6. Candidate extension: compare the original paper's deferred-tax book-equity convention with the modern benchmark convention. Hold all other construction choices fixed. Do not select an extension or tune baseline rules just to maximize correlation.
7. Produce the required report, reproducibility instructions, validations, AI-use disclosure, and documented Git milestones after confirming the course requirements.

## Sources inspected

- User-supplied `Paper1_FF93.pdf`, especially paper pp. 8–10 on six-portfolio construction and test portfolios.
- README and DATA_DICTIONARY in the course data packages.
- [Kenneth French factor definitions](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html).
- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), including the CIZ transition and construction changes. Modern published factors are a benchmark with methodological/vintage differences, not an exact original-paper target.
- [Course project page](https://yan-xiong-courses.protected-courses.workers.dev/quantitative-tools/project/): login screen reached; project instructions not yet accessible.
