# Reusable replication workflow

## Scope first

Write down the assigned paper, required period, raw inputs, target outputs and proposed extension before calculating results. Distinguish a historical numerical replication from a methodological replication on a modern sample. Fix the construction rules before comparing with the benchmark; do not tune filters to maximize correlation.

## Run sequence

1. Acquire authorized raw inputs outside the repository. Record filenames, schemas, dates, units and SHA-256 hashes. Keep a written data-access route, not credentials.
2. Run `python src/audit_inputs.py --data-root /path/to/downloads`. Inspect duplicates, classification conflicts, return missingness, accounting currencies, inactive-firm coverage and link types.
3. Run `python src/replicate.py --data-root /path/to/downloads`. Resolve effective-dated metadata; normalize monthly dates; screen the universe; construct company equity and lagged market weights; form BE and date-valid links; create June memberships and July–June portfolio returns.
4. Review `pipeline_audit.json`, annual formation coverage and all six-cell diagnostics. Check initial sample losses explicitly. Do not call an early missing month a zero return.
5. Run `python src/validate.py`. Independently verify saved-output arithmetic, matrix-form HAC and synthetic timing examples. Inspect the largest benchmark-gap months; do not equate high correlation with identical construction.
6. Interpret the extension using matched paired differences and uncertainty, not separate significance tests alone. Preserve null findings. State what trading costs, availability dates or vintage differences are unmeasured.
7. Run `python src/build_report.py`. Review every interpretation against the frozen result tables; changed results require changed prose. Inspect figures at readable size. The optional browser report uses the same reviewed rows and prose.
8. Commit meaningful milestones. Confirm no raw data, passwords or restricted URLs are tracked. A local commit is not publication. Choose private/public visibility according to licensing; grant teaching-team access and submit the repository link only after review.

One-command version: `python src/run_all.py --data-root /path/to/downloads --audit`.

## Reusable AI instruction

> Help me replicate the specified empirical construction using only the supplied inputs. First inspect the brief, schemas, units, dates and source methods. List assumptions that change eligibility, timing or weights. Write runnable code with explicit assertions and preserve raw files. Never fabricate unavailable observations, replace missing reconstructed returns with a benchmark, or tune the baseline to improve agreement. Save aggregate processed results, quantify benchmark errors over matched months, and test one economically motivated extension with uncertainty. Independently check key arithmetic with a different implementation. Explain failed attempts and corrections. Separate observed findings, interpretations and unresolved limitations. Produce a report, README, restricted-data access instructions and an honest AI-use disclosure. Do not publish or submit without my authorization.

## Human review before submission

The student should be able to explain BE/ME timing, the six portfolios, why SMB/HML do not subtract RF, the 30 missing months, the choice of NYSE breakpoints, and what the paired microcap test does and does not show. Review and retain the AI disclosure; do not claim independently completed work that has not been done.
