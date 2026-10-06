# Code ownership and reading order

The empirical implementation is in `src/`, not the optional web-viewer runtime.

1. `audit_inputs.py`: initial input profile, format checks and hashes.
2. `replicate.py`: screening, market equity, accounting/CCM joins, June memberships, lagged value weights, factors, sensitivities, inference and figures.
3. `validate.py`: independent saved-result checks and explicitly synthetic unit fixtures.
4. `build_report.py`: reviewed prose, table generation and companion evidence; guards against stale interpretations after result changes.
5. `run_all.py`: portable subprocess orchestration using the active Python executable.
6. `package_submission.py`: local archive and Git-bundle creation only; no upload.

The `report-app/` directory contains a copied OpenAI Data plugin viewer scaffold and shared React runtime. Its many infrastructure files are **third-party application machinery, not original econometric work by the student**. The task-specific web composition is `report-app/src/content/report/ReportContent.jsx`; reviewed evidence is `report-app/src/data.json`. The compiled `REPORT.html` is a convenience export. No web-runtime dependencies are needed to execute the core Python analysis, validate the results or read REPORT.md.

The empirical scripts and report were AI-assisted, as disclosed in REPORT.md. No implication of unaided student authorship is intended.
