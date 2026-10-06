# ECON6067 — Fama–French (1993) factor construction

**LEI Jinqiu · 3036762812 · MEcon**  
Completed local analysis: 6 October 2026. No GitHub publication or course submission has been performed.

## Start here

- [Empirical report](REPORT.md): approximately 3,200 words, with motivation, sample construction, formulas, benchmark comparison, independent extension, robustness, limitations, references and AI disclosure.
- [提交前请读](docs/提交前请读.md): concise Chinese explanation and submission checklist.
- [Data access](DATA_ACCESS.md): restricted input locations, fields, units and licensing.
- [Reusable workflow](WORKFLOW.md): procedure, AI instructions and human review.
- [Verified course brief](docs/course_requirements.md): assessed scope and deadline.

The completed local package includes Python code, aggregate processed CSVs, static figures, validation, and real Git history. An optional interactive companion lives in `report-app/`; it is not required to reproduce the empirical study. Its build passed, but browser automation was blocked by URL policy, so browser rendering and interactions are **not visually verified**. The Markdown report and static figures are the primary review artifacts.

## Main findings and scope

| Factor | Reconstructed months | Correlation with French | Monthly RMSE (bp) |
| --- | --- | --- | --- |
| MKT−RF | Jan 2000–Dec 2025: 312 | 0.999985 | 2.642 |
| SMB | Jul 2002–Dec 2025: 282 | 0.997312 | 18.357 |
| HML | Jul 2002–Dec 2025: 282 | 0.997206 | 23.118 |

This is a modern-sample methodological replication. The files do not cover the paper's 1963–1991 tests. SMB/HML's first 30 target months are unavailable under the two-observed-year accounting-history screen; they remain blank, not zero and not benchmark-filled. The baseline's NYSE size reference is the eligible accounting-linked population, a disclosed difference from the paper's all-NYSE wording.

The extension removes firms below the eligible-NYSE 20th size percentile while keeping the baseline breakpoints fixed. Excluding microcaps changes mean SMB by +0.92 bp/month (HAC t 0.33), not significant, and HML by −7.09 bp/month (t −4.25). These are paired construction differences, not causal effects or net trading returns.

## Reproduce from raw inputs

Tested with Python **3.10.7**, NumPy **2.2.6**, pandas **2.3.3**, matplotlib **3.10.9** on macOS. A fresh Python 3.10–3.12 environment is recommended. The study does not need SciPy or statsmodels.

From this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run_all.py --data-root /path/to/downloads --audit
```

On Windows activate `.venv\Scripts\activate` instead. Package installation needs normal internet/package-registry access. Computation thereafter is offline. Allow several minutes and several GB of memory; the stock CSV is about 1.24 GB. Raw files are read, never modified.

The data root must contain the two original package directories and filenames listed in [DATA_ACCESS.md](DATA_ACCESS.md). No licensed raw input is included. `--audit` repeats the initial audit and hashes; omit it on subsequent runs.

Individual stages:

```bash
python src/audit_inputs.py --data-root /path/to/downloads
python src/replicate.py --data-root /path/to/downloads
python src/validate.py
python src/build_report.py
```

Without raw files, `python src/validate.py` still checks the shipped aggregate evidence and timing fixtures; `python src/build_report.py` regenerates the report and PNGs from the shipped results. The prose is specific to the fixed supplied vintage. The report builder checks numerical agreement with its reviewed reference and stops on changed results: review/update the interpretation and reference deliberately rather than silently reusing stale claims.

## Contents and output contract

```text
src/                       Complete analysis, audit, validation and report generation
results/                   Aggregate processed inputs for review and inference
figures/                   Three PNG figures
REPORT.md                  English empirical report
DATA_ACCESS.md             Authorized input acquisition and schema
WORKFLOW.md                Reusable process and AI prompt
docs/                      Requirements, numerical report reference, review notes
report-app/                Optional reviewed-data web companion source
.git/                      Local meaningful commit history (or restore from bundle)
```

All monthly return columns in processed CSVs are **decimal fractions** unless their column explicitly says `pct` or `bps`. One basis point = 0.0001 in decimal-return units. Monthly dates are calendar month-ends. Empty initial SMB/HML cells are unavailable estimates.

- `constructed_factors.csv`: MKT_RF, SMB, HML on the full 312-month target grid.
- `benchmark_factors.csv`: supplied French factors and RF on the same grid; July 2026 database vintage.
- `six_portfolio_returns.csv`: SL, SN, SH, BL, BN, BH.
- `portfolio_month_diagnostics.csv`: cell counts, predetermined capital, weighted numerator, return and delisting count.
- `june_breakpoints.csv`, `formation_coverage.csv`: formation-year thresholds, counts and microcap shares.
- `ex_micro_factors.csv`, `original_BE_factors.csv`, `one_year_history_factors.csv`: named variants.
- `benchmark_comparison.csv`, `summary_statistics.csv`, `extension_tests.csv`, `sensitivity_comparison.csv`: final tables. Tests use HAC6, a finite-sample covariance correction and asymptotic normal p-values.
- `largest_benchmark_gaps.csv`, `market_diagnostics.csv`: transparent discrepancies.
- `input_audit.json`: initial profile and raw input hashes; not the final selection counts.
- `pipeline_audit.json`, `validation.json`: final exclusions/assertions and 13 independent/fixture checks.
- `report_sections.json`, `reviewed_snapshot.json`: report prose and aggregate web-report evidence.

## Optional web companion

The primary report is ordinary Markdown and can be reviewed on GitHub. The optional Data app needs the installed Data plugin's pinned authoring runtime to rebuild; it is not a Python analysis dependency. A portable compiled HTML is included in the delivery archive so recipients do not need that plugin to view it.

For a local source rebuild with Codex's bundled Node, substitute your own installation path:

```bash
node /path/to/data-analytics/scripts/data-app.mjs build --project-dir ./report-app --separate-data
python -m http.server 4193 --bind 127.0.0.1 --directory report-app/dist
```

Open `http://127.0.0.1:4193/`. Serve all of `dist/`, including its snapshot sidecar. Do not regenerate the companion with fake data or silently omit the reviewed snapshot. `build_report.py` updates its evidence while preserving the app ID; the UI then requires rebuilding. Static scientific PNGs are generated independently by the Python pipeline for the coursework files.

## Validation and limitations

Pipeline assertions and 13 additional checks pass, including month alignment, saved six-portfolio identities, independent matrix-form HAC and synthetic lag/gap cases. Static PNGs have been visually inspected. Browser visual/interaction verification remains unavailable; no claim is made that it passed.

The report explicitly discusses incomplete accounting prehistory, no actual filing-date test, modern versus original BE conventions, the restricted NYSE reference, representative share-class continuity, missing-return handling, unreconciled benchmark residuals and lack of transaction-cost analysis. High factor correlations are not an asset-pricing test.

## Git and submission

Existing commits record the actual audit, factor implementation and reporting stages. If the delivery archive provides a bundle instead of `.git/`, restore a normal repository first:

```bash
git clone ECON6067-FF93-history.bundle ECON6067-FF93-repository
```

Create your own empty GitHub repository, choose appropriate visibility, and grant the teaching team access. Then, **after reviewing the files and licensing**, run from the repository:

```bash
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

Replace placeholders with your chosen account/repository. These commands have **not** been run on your behalf. Do not include raw data, the course password, restricted download links, the paper PDF or your virtual environment. A private repository with teaching-team access is the conservative default; public visibility also exposes the student name/ID in this coursework.

The course requires an accessible GitHub URL, not merely a ZIP. Deadline: **18 October 2026, 23:59 Hong Kong**, according to the authenticated project brief. Review the final course page and submit the URL yourself, or explicitly authorize a later publication step with account, repository and visibility specified.

## AI disclosure

Codex assisted with the analysis and writing. Executed evidence, checks and corrected errors are documented in REPORT.md §8. Student review remains necessary; do not remove the disclosure or imply unperformed independent work.
