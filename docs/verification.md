# Verification record — 6 October 2026

**Ready for student review with disclosed limitations.** This is not certification of exact historical replication, full early-period coverage or submission.

## Executed

- Raw-input pipeline executed successfully, then rerun end-to-end through `src/run_all.py` with the supplied files. Recomputed factor, extension and summary results agree with the reviewed numerical reference at tolerance 1e-8.
- All production assertions passed: security-month uniqueness, accounting precedes June, formation merge cardinality, nonempty cells, factor identities and 312-month calendar grid.
- `src/validate.py`: 13 additional checks passed. These cover saved aggregate arithmetic, independently implemented matrix-form HAC and synthetic portfolio timing/missing-history examples. Synthetic rows are test fixtures only.
- Inspected all three final PNG figures: cumulative factors, benchmark scatter plots and microcap comparison. Labels, legends, date ranges, lines and scatter marks are visible; comparison lines distinguish series by solid/dashed style in cumulative charts. Different factors use different vertical scales.
- Optional report app built through the pinned Data runtime; authored-content checks passed. Its four generated tables have the expected source-query mappings. These are source/build checks, not browser rendering checks.
- Scanned project text for the supplied password, raw machine paths and restricted download links; none were retained in authored deliverables. The app runtime's generic Google Drive hostname classifier is not a data download link.

## Corrected defects

Raw last-trading-day timestamps initially aligned with only 221 calendar-month benchmark dates instead of 312. The pipeline now normalizes dates after effective-date resolution and the independent validation requires all benchmark months. No benchmark returns were substituted into the reconstruction.

Initial classification screening and portfolio construction were separated: the audit is an initial profile, whereas `pipeline_audit.json` records final eligible counts and temporal rules. Accounting conventions and missing prehistory are explicit. A local SciPy binary problem was avoided, with the small HAC calculation independently validated without SciPy.

## Not verified / not performed

- Browser automation was blocked by its URL security policy for the local report. No workaround was used. Desktop/narrow visual layout, hover, source-menu and interactive controls remain unverified. Use the Markdown report and inspected PNGs as the primary coursework artifacts.
- No independent vendor re-extraction, complete constituent-level attribution of benchmark gaps, filing-date availability test, trading-cost calculation, or replication of all original FF93 pricing regressions.
- No GitHub repository creation, publication, permission change or final course submission. The local archive is a review package, not evidence of submission.

Core analytical limitations and exact covered months are disclosed in REPORT.md. The student should review both the interpretation and AI-use disclosure before publication or submission.
