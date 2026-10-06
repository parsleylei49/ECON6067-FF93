"""Build the academic Markdown report and reviewed companion-app snapshot."""
from pathlib import Path
import json
from datetime import datetime, timezone
import argparse
import pandas as pd
from replicate import plot_all

ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
parser=argparse.ArgumentParser()
parser.add_argument('--complete-app',action='store_true',help='Mark optional app authoring complete; does not certify browser checks')
args=parser.parse_args()
def read(name): return pd.read_csv(R/(name+'.csv'))
def table(frame, columns):
    rows=['| '+' | '.join(columns.values())+' |','| '+' | '.join(['---']*len(columns))+' |']
    for _,r in frame.iterrows():
        rows.append('| '+' | '.join((f'{r[c]:.2g}' if c=='p_HAC6' else f'{r[c]:.3f}') if isinstance(r[c],float) else str(r[c]) for c in columns)+' |')
    return '\n'.join(rows)

# The interpretation is reviewed for this fixed input vintage. Do not silently
# retain its numerical claims after a data refresh or construction change.
reference=json.loads((ROOT/'docs/report_numeric_reference.json').read_text())
for name,rows in reference.items():
    try:
        pd.testing.assert_frame_equal(read(name),pd.DataFrame(rows),check_dtype=False,atol=1e-8,rtol=1e-8)
    except AssertionError as error:
        raise RuntimeError('Results changed: review report prose and deliberately update docs/report_numeric_reference.json before regenerating.') from error
comparison=read('benchmark_comparison');summary=read('summary_statistics');extension=read('extension_tests')
coverage=read('formation_coverage');sensitivity=read('sensitivity_comparison')
audit=json.loads((R/'pipeline_audit.json').read_text())
factors=pd.read_csv(R/'constructed_factors.csv',index_col=0,parse_dates=True)
benchmark=pd.read_csv(R/'benchmark_factors.csv',index_col=0,parse_dates=True)
ex=pd.read_csv(R/'ex_micro_factors.csv',index_col=0,parse_dates=True)
plot_all(factors,benchmark,{'ex_micro':ex},ROOT/'figures')
full=extension[extension.period.eq('full')].copy()
paired=full[full.series.eq('paired_difference')].set_index('factor')
micro_share=coverage.microcap_count_share.mean()*100
micro_cap=coverage.microcap_capital_share.mean()*100
corr=factors[['SMB','HML']].corr().iloc[0,1]
sections=[]
def add(id,title,text,queries=(),charts=()):
    sections.append({'id':id,'title':title,'text':text.strip(),'queries':list(queries),'charts':list(charts)})

add('summary','Executive summary',f"""
## Executive summary

This project reconstructs the equity factors of Fama and French (1993) from the supplied CRSP and Compustat extracts and tests whether excluding microcaps changes the size premium. It is a **modern-sample methodological replication**, not a reproduction of the paper's 1963–1991 numerical tables.

- The reconstructed market excess return covers January 2000–December 2025 (312 months). SMB and HML cover July 2002–December 2025 (282 months). Missing pre-2000 accounting history prevents a defensible full-period size/value reconstruction under the two-observed-year screen; the initial 30 months remain missing.
- Correlations with the supplied Kenneth French benchmark are **0.999985 for MKT−RF, 0.997312 for SMB and 0.997206 for HML**. Monthly root-mean-square differences are **2.64, 18.36 and 23.12 basis points**, respectively. High correlations do not imply an exact match.
- Excluding stocks at or below the eligible-NYSE 20th size percentile raises average SMB by only **0.92 basis points per month** (paired HAC t = 0.33; p = 0.741). The data do not support the claim that microcaps drive a positive size premium in this sample. The same exclusion lowers average HML by **7.09 basis points** (t = −4.25), a composition sensitivity rather than a causal effect.
""",['comparison','extension'])

add('motivation','1. Question and paper',"""
## 1. Research question and original paper

Fama and French (1993), *Common risk factors in the returns on stocks and bonds*, Journal of Financial Economics 33, 3–56, construct portfolios intended to capture common variation associated with market exposure, firm size and book-to-market equity. Their broader study also examines bond factors. This project's assigned core is the construction of the three equity factors, not the paper's bond analysis or all 25-portfolio pricing regressions.

SMB compares small with big firms while balancing the three book-to-market groups. HML compares high with low book-to-market firms while balancing the two size groups. Independent sorts help distinguish the two characteristics, although they do not guarantee statistically independent factors. The pricing interpretation would require additional asset-pricing tests; agreement with a published factor series alone does not establish that risk explains expected returns.

The replication question is whether the prescribed June 2×3 procedure reproduces modern published factors using the course extracts. The independent extension asks: **Does the measured size premium depend on the smallest firms?** The practical motivation is that a factor dominated by very small firms may be less useful for implementation, although this project does not estimate liquidity or trading costs.
""")

add('data','2. Data and sample',f"""
## 2. Data, variables and sample

The supplied monthly CRSP file contains 2,423,212 rows and 2,393,591 unique security-month keys, January 2000–December 2025. Compustat contains 301,565 annual statement records dated 2000–2025, including active and inactive firms, USD and CAD records. CCM contains 39,761 historical link rows. The supplied French file identifies its vintage as the July 2026 CRSP database; only its monthly observations and the relevant sample are used. French factors and RF are divided by 100 to convert percentage units to decimal returns.

### Security data

Repeated records agree on core prices and returns, but 1,542 duplicated keys disagree on security metadata. Identical selected rows are removed, then security information must be valid at the earlier of the raw observation date and security end date. After this historical classification check, dates are normalized to calendar month-end. The earlier date handles records whose security life ends before month-end; it is not a fill-forward of expired classifications. Unresolved duplicate security-months cause an error.

The universe requires US-incorporated ordinary common equity, NYSE/AMEX/NASDAQ primary exchange, regular-way conditions and active trading status (`EQTY`, `COM`, `NS`, `CORP/ACOR`, `Y`, `N/A/Q`, `RW`, `A`). The final screen retains **{audit['eligible_security_months']:,} security-months**, of which {audit['eligible_missing_returns']} have missing returns. Both active and subsequently inactive accounting firms remain eligible. Missing returns are not replaced by zero.

Market equity is `abs(MthPrc) × ShrOut / 1000`, measured in millions of dollars because CRSP shares are in thousands and Compustat amounts are in millions. Company-level equity sums eligible share classes within PERMCO; the largest class, with PERMNO as a deterministic tie-breaker, represents the company for sorting and returns. This conventional representative-class approximation can lose continuity when the largest class changes.

### Accounting and links

Use consolidated, standard-format industrial statements in USD; for multiple statement dates within a calendar year, retain the latest. Preferred equity uses redemption value, then liquidation value, then par value; all missing values are treated as zero and counted in the audit. Stockholders' equity uses `seq`, then `ceq + pstk`, then `at − lt`. Positive book equity is required. Modern baseline BE equals equity less preferred equity. The original-paper variant adds available deferred taxes and investment tax credits (`txditc`, missing treated as zero).

For June of year t, use a statement ending in calendar year t−1, December t−1 market equity and June t size. CCM links must have LC/LU type, P/C primary status and validity on the June formation date. Multiple eligible candidates are resolved by P before C, LC before LU, then latest statement and gvkey; no duplicate linked security-year candidates arise here. Actual filing timestamps and historical database entry dates are unavailable, so the calendar-year lag is a convention, not proof that every statement was publicly available by June.

At least two distinct accounting years observed in the extract are required, as a proxy for the paper's two-year Compustat-history rule. Because records start in 2000, the first baseline June formation is 2002. This also penalizes some genuinely seasoned firms near the left boundary. June 2000 would require December 1999 market equity and 1999 accounting information, which are absent. Relaxing history to one observed year starts in July 2001 but still cannot reconstruct the full requested 2000–2025 window.

There are **{audit['baseline_formation_firm_years']:,} eligible firm-years** across 24 June formations. Each monthly cell contains at least **{audit['min_cell_n']} firms**. Exact annual coverage, breakpoints, retained counts and input SHA-256 hashes are saved in `results/`. Preliminary audit counts are not the final pipeline counts because the temporal-resolution rule was refined after auditing.
""",['coverage'])

add('method','3. Construction and inference',"""
## 3. Factor construction and inference

Each June, compute the median size and the 30th/70th book-to-market percentiles using eligible NYSE firms. Size is small at or below the median and big otherwise; value groups are low at or below the 30th percentile, neutral up to the 70th and high above it. Applying both independent assignments produces SL, SN, SH, BL, BN and BH. Percentiles use linear interpolation.

The baseline estimates both sets of breakpoints within the positive-BE, accounting-linked sample. The original paper describes ranking all NYSE stocks for size before the accounting screen; this restricted breakpoint reference is a disclosed approximation, not an exact implementation of that particular wording. Memberships are fixed from July through June; no current-month return is used to set that month's weight.

For firm i and holding month m, the weight is June market equity multiplied by the product of (1 + ex-distribution return) from July through m−1. July uses June equity directly. The cell return is the sum of weight × total return divided by usable total weight. A broken July-to-current-month sequence, missing prior ex-return, nonpositive weight or missing current total return excludes that observation. Remaining weights are normalized; there is no claim that missing delisting returns have been recovered. In total 278 candidate holding observations are excluded by these rules.

`SMB = (SL + SN + SH)/3 − (BL + BN + BH)/3`

`HML = (SH + BH)/2 − (SL + BL)/2`

The market return is computed separately from eligible common securities using prior-month market-equity weights, including negative-BE or unlinked firms. Only January 2000 uses the supplied previous-cap field after verifying its date is the preceding month. MKT−RF subtracts the supplied RF; SMB and HML are already long-short returns and do not subtract RF again. The supplied CRSP value-weighted market index is retained for diagnostics, not substituted as the reconstruction.

CIZ monthly returns already incorporate delisting treatment; a second delisting-return adjustment would double count it. The construction retains 837 delisting-flagged holding observations. This does not prove that every delisted security is observed after universe and missing-data screens. French's current CIZ series also differs from older FIZ series in dividend reinvestment timing; comparisons hold the supplied benchmark vintage fixed.

Summary means are arithmetic monthly means; annual volatility is monthly sample standard deviation × sqrt(12). Inference uses intercept-only Newey–West covariance with six Bartlett lags and n/(n−1) finite-sample correction. Two-sided p-values and 95% intervals use a normal reference distribution, not an exact finite-sample t law. This is descriptive HAC inference, not a test of causal identification. Cumulative figures plot product(1 + factor return) − 1 with a common start date within each comparison. They are gross theoretical factor-return indices, not directly investable wealth or compounded market total returns.
""")

add('replication','4. Replication results',f"""
## 4. Replication results and comparison

### Benchmark alignment

{table(comparison,{'factor':'Factor','n':'Months','correlation':'Correlation','mean_difference_bps':'Mean gap (bp/month)','RMSE_bps':'RMSE (bp/month)'})}

The mean gap is reconstructed minus benchmark. MKT−RF is compared over January 2000–December 2025; SMB/HML over July 2002–December 2025. No unmatched month is treated as zero. Calendar-month normalization is essential: joining raw trading dates to calendar month-ends would incorrectly discard 91 market observations.

### Summary statistics

{table(summary,{'factor':'Factor','series':'Series','n':'Months','mean_monthly_pct':'Mean (%/month)','vol_annual_pct':'Volatility (%/year)','t_HAC6':'HAC t'})}

The modern reconstructed size and value means are not distinguishable from zero with this estimator. Their small estimated means do not imply that the factors lack common variation or pricing relevance. The reconstructed SMB–HML correlation is {corr:.3f}; the paper reports −0.08 for its historical sample. The size and value factor indices can therefore fluctuate considerably despite small full-sample arithmetic means.

Fama and French's Table 2/discussion on printed pp. 13–14 reports historical monthly mean MKT−RF, SMB and HML of 0.43%, 0.27% and 0.40%, respectively. The corresponding modern estimates here are 0.609%, 0.021% and −0.033%. This comparison is about changed sample estimates, not a failed match to the original period: the supplied extracts do not overlap July 1963–December 1991. It cannot distinguish structural change from sampling variation, database revisions or construction differences.

The largest absolute monthly benchmark gaps are 13.08 bp for MKT−RF (November 2025), 62.92 bp for SMB (November 2024), and 84.44 bp for HML (November 2024). `largest_benchmark_gaps.csv` identifies the worst three months for each factor. High correlation coexists with nontrivial monthly errors. Potential sources are eligibility and breakpoint populations, incomplete prehistory, representative share-class changes, accounting fallbacks and different database vintages. This project has not attributed each residual to a specific security; those explanations remain hypotheses rather than proven reconciliations.
""",['comparison','summary'],['market','smb','hml'])

add('extension','5. Independent extension',f"""
## 5. Independent extension: do microcaps drive the size premium?

Define microcaps at each June formation as firms at or below the **20th percentile of eligible NYSE size**. Remove these firms from the six portfolios but keep the baseline median-size and book-to-market breakpoints fixed. This isolates a membership/reweighting change from moving the category thresholds. All other accounting, return and timing rules remain unchanged. The benchmark baseline was not selected by searching for the strongest extension result.

Across June formations, microcaps average **{micro_share:.1f}% of eligible firm counts** but only **{micro_cap:.2f}% of their June market equity** (unweighted averages of annual shares). They can still affect SMB/HML because the factors average portfolios rather than weight every constituent by its share of the entire market.

{table(full,{'factor':'Factor','series':'Series','mean_monthly_pct':'Mean (%/month)','vol_annual_pct':'Volatility (%/year)','t_HAC6':'HAC t','p_HAC6':'p (normal)'})}

The paired difference is ex-microcap minus baseline, using all 282 matched months. For SMB it is **+0.92 bp/month**, with a 95% HAC interval of **[−4.51, +6.35] bp/month**. Exclusion reduces annualized SMB volatility from 8.68% to 8.29%, but the mean change is not statistically distinguishable from zero. This rejects neither zero effect nor economically modest effects; it does not establish equivalence. In this sample a positive size premium does not appear to be concentrated in microcaps, and the baseline premium itself is weak.

For HML the paired change is **−7.09 bp/month**, 95% interval **[−10.36, −3.82] bp/month**. Multiplying the monthly arithmetic change by 12 gives roughly −0.85 percentage points per year, not a compounded annual return. The direction suggests that including microcaps makes measured value returns less negative in this construction. It does not show that removing microcaps causes returns to fall in a tradable counterfactual.

As a stability check, split the sample at January 2014: July 2002–December 2013 (138 months) and January 2014–December 2025 (144 months). The SMB changes are +0.76 and +1.06 bp/month, neither significant; HML changes are −9.12 and −5.14 bp/month, with HAC t statistics −3.46 and −2.59. The split is a descriptive roughly balanced early/late comparison, not an externally dated economic regime. The extension was developed during the project and is not preregistered; subperiod tests are exploratory and unadjusted for multiple comparisons. Liquidity, shorting costs and turnover remain unmeasured.
""",['extension','coverage'],['micro-smb','micro-hml'])

add('validation','6. Robustness and validation',f"""
## 6. Robustness, validation and limitations

{table(sensitivity[sensitivity.variant.ne('ex_micro')],{'variant':'Construction variant','factor':'Factor','n':'Matched months','mean_shift_bps':'Mean shift vs baseline (bp)','RMSE_vs_official_bps':'RMSE vs benchmark (bp)'})}

Adding deferred taxes, as in the original paper, changes HML more noticeably and worsens its benchmark RMSE from 23.12 to 59.82 bp. That is consistent with a modern benchmark using a different BE convention, but it does not isolate every vintage difference. Relaxing the history rule to one observed year changes full-overlap means by less than 0.55 bp/month and leaves benchmark RMSE close to the baseline. Comparisons in this table use the common 282 months; the longer one-year-history series is separately saved.

The pipeline checks historical-link timing, unique security-month and formation keys, nonempty cells, positive usable weights, factor identities and the complete 312-month output grid. A separate validation script independently reconstructs the saved factors from the six portfolios and verifies the extension's HAC standard errors using a full Bartlett covariance matrix. Synthetic two-firm examples verify June weights, lagged ex-return growth and broken-history handling; these fixture rows never enter empirical results. Thirteen additional checks pass. This is not an independent reconstruction of the complete vendor database.

Important qualifications remain. First, full 2000–2025 SMB/HML coverage is unavailable without earlier raw inputs; backfilling with benchmark returns would not be replication. Second, the two-observed-year rule is an imperfect proxy for time on Compustat and can create left-truncation selection. Third, statement availability is not checked against filing dates, and revised accounting data can contain hindsight. Fourth, the eligible-NYSE breakpoint reference differs from the paper's all-NYSE size wording. Fifth, share-class representation, strict active-trading screens, missing-value exclusions, zero-preferred fallback and modern CIZ conventions can change the universe and weights. Finally, benchmark agreement validates construction approximately, not the factor model's explanatory or causal validity.
""",['sensitivity'])

add('conclusion','7. Conclusion',"""
## 7. Conclusion

The supplied data reproduce modern equity-factor movements closely after careful unit conversion, historical classification resolution and monthly date alignment. They do not support exact historical-table reproduction or full 2000–2025 size/value coverage. The independent microcap exercise finds little evidence of a mean SMB change but a material negative HML shift when the smallest firms are excluded. Thus, construction details matter even when the usual size-premium narrative is not supported in the chosen sample.

The most useful further improvement would be to obtain pre-2000 CRSP/Compustat history and independently reconcile the largest benchmark-gap months at the constituent level. This is a limitation of the delivered study, not evidence that missing returns are zero or that published factors should be copied into the reconstruction.
""")

add('ai','8. AI-use disclosure',"""
## 8. AI-use disclosure and reproducibility

OpenAI Codex assisted with reading the course brief and paper, auditing supplied data, implementing the factor pipeline, generating figures and tables, writing this report and checking the results. The empirical estimates come from executed code on the supplied files, not from invented examples or a language model's remembered factor returns. AI-authored analysis remains subject to the student's review; this disclosure does not claim that the student has independently performed every check.

Concrete corrections were made during development. Raw trading-day dates initially failed to align with calendar month-end benchmark labels, losing 91 matched market observations; dates were normalized and a 312-month test added. Blind first-row deduplication was rejected because historical security classifications conflict. A blanket month-end classification rule was refined to account for securities ending within a month. A single BE convention was replaced by an explicit modern baseline and original-tax-addback sensitivity. Missing early factors were left blank rather than copied from French. A broken local SciPy binary was avoided by implementing the small intercept-only HAC calculation directly and checking it independently.

Run `python src/replicate.py --data-root /path/to/downloads`, `python src/validate.py`, then `python src/build_report.py`. Inputs and access restrictions, exact environment versions, output schemas and review steps are documented in README.md, DATA_ACCESS.md and WORKFLOW.md. Raw licensed data, the course password and the paper PDF are not included in the repository. Git commits record actual audit, implementation and reporting stages. Local packaging is not GitHub publication or submission.
""")

add('references','References',"""
## References

1. Fama, E. F. and French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*, 33(1), 3–56. [DOI](https://doi.org/10.1016/0304-405X(93)90023-5). Supplied PDF inspected, especially printed pp. 8–10 and 13–14.
2. Kenneth R. French Data Library. [Three-factor definitions](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library/f-f_factors.html) and [six size/book-to-market portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios.html). Methods consulted 6 October 2026; numerical benchmark is the supplied July 2026 vintage.
3. Kenneth R. French Data Library. [Data notes and historical construction changes](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), including the CIZ transition and post-1992 deferred-tax convention.
4. WRDS. [CIZ event-study macro documentation](https://wrds-www.wharton.upenn.edu/pages/wrds-research/macros/run-an-event-study-ciz-format-macro/), on delisting-return incorporation in CIZ.
5. ECON6067. [Final-project brief](https://yan-xiong-courses.protected-courses.workers.dev/quantitative-tools/project/), authenticated course page consulted 6 October 2026; supplied data-package README and DATA_DICTIONARY files. Access-controlled data-download links are deliberately omitted.
""")

title='Reconstructing Fama–French equity factors: a modern-sample replication and microcap extension'
report=f'# {title}\n\nLEI Jinqiu · Student ID 3036762812 · MEcon · ECON6067\n\n6 October 2026\n\n'
for section in sections:
    report+=section['text']+'\n\n'
    if section['id']=='replication':
        report+='![Figure 1. Matched-sample compounded factor indices](figures/factor_cumulative.png)\n\n![Figure 2. Monthly factor agreement; diagonal is equality](figures/factor_scatter.png)\n\n'
    if section['id']=='extension':
        report+='![Figure 3. Microcap exclusion with original breakpoints fixed](figures/microcap_extension.png)\n\n'
(ROOT/'REPORT.md').write_text(report)
(R/'report_sections.json').write_text(json.dumps(sections,ensure_ascii=False,indent=2)+'\n')

queries={}
for q,filename in [('comparison','benchmark_comparison'),('summary','summary_statistics'),('extension','extension_tests'),('coverage','formation_coverage'),('sensitivity','sensitivity_comparison')]:
    queries[q]={'rows':read(filename).to_dict('records'),'source':{'label':filename.replace('_',' '),'files':['results/'+filename+'.csv'],'period':{'start':'2000-01-01' if q in ['comparison','summary'] else '2002-07-01','end':'2025-12-31'},'evidenceFlow':[{'title':'Restricted raw inputs','detail':'Course CRSP monthly stocks, Compustat annual statements and CCM historical links; no raw rows embedded.'},{'title':'Reconstruction','detail':'Run src/replicate.py, followed by src/validate.py. Returns are decimals; summary means are monthly percent; comparison gaps are basis points.'}],'caveats':['SMB/HML baseline starts July 2002. Market starts January 2000. Benchmark vintage July 2026.'],'metricDefinitions':[{'label':'Units and sample','definition':'Monthly matched observations. One basis point = 0.01 percentage points. Annual volatility = monthly sample SD × sqrt(12). HAC6 uses Bartlett lags and normal-reference p-values.','componentIds':[s['id'] for s in sections if q in s['queries']]}]},'methods':[{'language':'Python','code':'python src/replicate.py --data-root /path/to/downloads\npython src/validate.py'}]}

for q,component in [('comparison','replication:table-0'),('summary','replication:table-1'),('extension','extension:table-0'),('sensitivity','validation:table-0')]:
    queries[q]['source']['metricDefinitions'][0]['componentIds'].append(component)

for q,f,other in [('market','MKT_RF',benchmark),('smb','SMB',benchmark),('hml','HML',benchmark),('micro-smb','SMB',ex),('micro-hml','HML',ex)]:
    z=pd.concat([factors[f].rename('Reconstructed' if other is benchmark else 'Baseline'),other[f].rename('French benchmark' if other is benchmark else 'Exclude microcaps')],axis=1).dropna()
    cum=((1+z).cumprod()-1)*100
    rows=[]
    for dt,row in cum.iterrows():
        for label,val in row.items(): rows.append({'date':str(dt.date()),'series':label,'index_pct':float(val),'factor':f,'monthly_return_pct':float(z.loc[dt,label]*100)})
    queries[q]={'rows':rows,'source':{'label':f+' compounded factor-return index','files':['results/constructed_factors.csv','results/benchmark_factors.csv' if other is benchmark else 'results/ex_micro_factors.csv'],'period':{'start':str(z.index.min().date()),'end':str(z.index.max().date())},'evidenceFlow':[{'title':'Monthly factors','detail':'src/replicate.py constructs eligible value-weighted portfolios. Each comparison uses only jointly observed months.'},{'title':'Index calculation','detail':'For each series, calculate 100 × (cumulative product of (1 + monthly decimal factor return) − 1).'}],'metricDefinitions':[{'label':'Compounded factor index (%)','definition':'100 × [product(1 + factor return) − 1]. A gross theoretical index, not directly investable wealth. Separate vertical scales across factors.','componentIds':['chart-'+q]}],'caveats':['SMB/HML begins July 2002, not January 2000. No fees, shorting costs or trading costs.']}}
snapshot={'surface':'report','title':title,'generatedAt':datetime.now(timezone.utc).isoformat(),'status':'reviewed','buildStatus':'creating','report':{'asOf':'2025-12-31'},'filters':[],'queries':queries,'reportSections':sections}
# Preserve app identity and progress if refreshing an existing companion.
app=ROOT/'report-app/src/data.json'
if app.exists():
    old=json.loads(app.read_text());snapshot['id']=old['id'];snapshot['buildStatus']='complete' if args.complete_app else 'updating'
    app.write_text(json.dumps(snapshot,ensure_ascii=False,allow_nan=False)+'\n')
(R/'reviewed_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,allow_nan=False)+'\n')
print('Built REPORT.md, reviewed_snapshot.json and chart files.')
