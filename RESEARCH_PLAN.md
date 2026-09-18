# Bullpen Ledger: analysis specification

Written before fitting models, September 17, 2026.

Question: Does recent recorded pitching workload improve predictions of a reliever's next appearance beyond prior performance and entry context?

Primary outcome: appearance (strikeouts − unintentional walks) / batters faced. Intentional walks are removed from the numerator, but all batters faced remain in the denominator. This is a performance proxy, not measured fatigue.

Development: 2023–2024 MLB regular season. Locked chronological evaluation: 2025. No random row split. Pre-appearance features only. Pitch counts cover recorded game pitches, not warm-ups or bullpen sessions. Context model versus the same model with workload features. Fixed ridge penalty; no test-year tuning.

Workload: complete calendar days without pitching; pitches in prior 1, 3 and 7 calendar days; previous-day 20+ pitch flag; consecutive-day usage. Pitching workload includes starts as well as relief appearances. Double appearances on the same date and suspended-game outcomes excluded from modeling; actual dated plays retained in workload histories.

Cohort: relief appearances with positive batters faced, at least five prior relief appearances that season, and a pitcher-majority retrospective season role (pitching games at least half of all games played). The role cohort uses full-season classification, so evaluation applies to established pitchers, not a prospect eligibility model.

Inference: pitcher-season fixed effects, batters-faced weighting, pitcher-clustered standard errors; descriptive associations, not causal fatigue effects. Predictive evaluation uses weighted RMSE and paired pitcher bootstrap uncertainty. Report lack of improvement if present.

Supplement: Toronto 2024–2025 Statcast four-seam velocity relative to a pitcher's prior five Toronto four-seam appearances. Keep pitch type constant, require at least five measured four-seam pitches in the current appearance and three earlier qualifying appearances. Exploratory only; no injury inference.

Deliverables: interactive historical appearance board, workload/performance comparison, held-out model evaluation, Toronto velocity panel, methods, reproducible scripts and source manifest. No roster availability claims and no medical or injury-risk score.

## Revision 2: diagnostic extension

Requested after reviewing version 1. Keep both predictive models and the 2025 evaluation population fixed. These additional checks are **post-hoc diagnostics**, not a new untouched test. Evaluate frozen predictions in late/close entries (inning 7+ and absolute margin at most 3), appearances with at most six MLB off-days, and shorter outings (at most six BF, an outcome-conditioned descriptive subset). Also evaluate equal-appearance weighting and month-level stability. Use paired pitcher-bootstrap intervals; do not select or refit a model using these results.

Add an as-of-appearance pitcher dossier using strictly earlier dated MLB pitch records; flag gaps of 14+ MLB off-days as incomplete recovery context. This threshold is a display convention, not a validated physiological cutoff. Audit the Toronto name join across both source seasons and assess pitch-feed discrepancies without replacing the original velocity analysis.
