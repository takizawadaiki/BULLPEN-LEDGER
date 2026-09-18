# Bullpen Ledger

**Does recent workload improve the prediction of a reliever's next appearance?**

An independent baseball-operations research project by Daiki Takizawa. Public data, chronological testing, uncertainty and an interactive appearance board. No claim of affiliation with MLB or a club.

## Findings

38,925 eligible relief appearances across 2023–2025; 25,844 for development and 13,081 for evaluation in 2025. The outcome is (strikeouts − unintentional walks) / all batters faced, abbreviated K−uBB rate here.

The context model's held-out weighted RMSE was **26.474 percentage points**, compared with **26.480** after adding workload. The change was **+0.00589 pp** (positive is worse); the paired pitcher-bootstrap 95% interval was **[−0.00078, +0.01287] pp**. This model provided no clear incremental predictive benefit. This does not establish that fatigue is absent or unimportant.

The Toronto four-seam supplement has 382 qualifying appearances over 2024–2025. In 2025, the 39 qualifying zero-MLB-off-day appearances averaged approximately **−0.142 mph** versus their prior-appearance baseline (95% pitcher-bootstrap interval approximately **−0.357 to +0.161 mph**). This is exploratory and not a causal estimate.

## Use the dashboard

Open index.html directly, or run `python3 -m http.server 8770` in this directory and visit http://localhost:8770/. All dashboard assets are local, with no API key or build step. Select a club, month, pitcher and workload lens. Click an appearance to inspect the previous seven dates. Outcomes are behind an explicit disclosure. The board contains actual appearances, not all roster members, and does not identify who was available but unused.

For GitHub Pages, upload this folder's **contents** (including data/) to a new public repository, with index.html at the publishing root. Suggested repository: bullpen-workload-analysis. Enable Pages for main and /(root). Do not upload raw downloads: the reproducible download script obtains them. The site has not been published automatically.

## Reproduce

Use Python 3.9+ and the versions in requirements.txt. From this folder:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download.py --raw raw
python analyze.py --raw raw
python toronto.py --raw raw
python diagnostics.py --raw raw
python build_data.py
python verify.py --raw raw
```

Download size and source availability can change. The downloader caches existing files and requests sequentially. The provided source manifest records the exact files used in this analysis. The raw folder and Python environment should not be published. Chart.js 4.4.0 is vendored under its MIT license.

## Design choices

- Development seasons: 2023–2024. Coefficients and penalty are frozen before evaluation on 2025. No test-year hyperparameter selection.
- Pre-entry context: prior performance, entry inning, absolute score margin capped at 10, inherited runners, home/away, temperature and month. These are **entry-time**, not day-before, predictions.
- Workload features: rest-group indicators, recorded pitches in the prior 3 and 7 calendar days (per 10 pitches), 20+ pitches the previous day, pitching on both prior dates. Workload windows include starts, trades and actual dates of suspended-game continuation.
- A recorded MLB off-day does not establish physical rest: minors, rehab, warm-ups and bullpen sessions are not measured.
- Expanding baseline: earlier non-suspended relief outcomes in the same season, plus 100 pseudo-batters with 15% K−uBB. The fixed prior is a transparent regularizer, not an estimated physiological expectation. Earlier 2025 data updates this baseline but never model coefficients.
- Cohort: positive-BF relief appearances after five prior season relief appearances. Players must pitch in at least half their full-season games. This retrospective role filter restricts the target population; it is not a live role classifier. A reliever with fewer than five prior outings does not enter the board. Position players are excluded by the role filter.
- Suspended-game outcomes and pitcher-days with two appearances are excluded from modeling. Their dated pitches still contribute to later workload. Counts use Retrosheet nump, with empty counts on non-PA events treated as zero; every completed PA has a count in the source files.
- The two predictive models are standardized ridge regressions (alpha=100), weighted by BF. Standardization and missing-temperature median use development data only. No per-pitcher injury score, medical conclusion or deployment recommendation is produced.
- Separate development associations: weighted pitcher-season fixed effects, pitcher-clustered covariance, degrees-of-freedom correction for absorbed intercepts, and cluster-t intervals. Workload features overlap, so partial effects are conditional and may be unstable. They are not isolated policy effects.
- Bootstraps: random seed 71. Paired prediction-error comparison: 1,000 pitcher clusters; descriptive baseline differences: 500; Toronto velocity: 1,000. Pointwise intervals are not multiplicity-adjusted. Predictions are single-appearance performance proxies, not probabilities.
- Toronto supplement: measured FF pitches only, speed between 70 and 110 mph; at least five per appearance; at least three earlier qualifying Toronto relief appearances; baseline uses up to five, equally weighted. Resets by year. A traded pitcher's non-Toronto pitch history is absent. Statistical intervals reflect a small number of pitchers.

## Key limitations

Observed deployment is selected by managers: fatigued pitchers may already have been rested. No randomized rest schedule or causal identification. No private recovery measures. Opponent quality, batter handedness, pitch shape, exact elapsed hours and travel are omitted. One holdout season and one model family cannot rule out useful workload signals in better data or different targets. Short-appearance rates are noisy, and BF weighting means long appearances contribute more.

The 2025 held-out data is now examined. Any new model developed using these findings requires another genuinely untouched period or an explicitly nested validation design; do not describe further tuning against 2025 as a fresh test.

## Source audit

Retrosheet: https://www.retrosheet.org/downloads/csvdownloads.html and https://www.retrosheet.org/downloads/csvcontents.html

Baseball Savant: https://baseballsavant.mlb.com/statcast_search and https://baseballsavant.mlb.com/csv-docs

47,300 Toronto Statcast rows from 324 games. After removing ambiguous same-date pitcher appearances and suspended-game outcomes, 1,436 pitcher-date matches were obtained. Recorded pitch counts agree exactly for 1,347 (93.8%) and within two for 1,387. The remainder demonstrates that feeds are not identical; velocity results use measured four-seams, while workload is defined consistently from Retrosheet. IDs are joined via normalized exact names and dates, with unique pitcher-date checks. No fuzzy matching is used.

The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at 20 Sunset Rd., Newark, DE 19711.

## Files

- `RESEARCH_PLAN.md`: specification written before fitting; not an externally registered study.
- `RESEARCH_BRIEF.md`: concise interpretation and interview discussion guide.
- `download.py`, `analyze.py`, `toronto.py`, `diagnostics.py`, `build_data.py`, `verify.py`: reproduction pipeline.
- `data/summary.json`: results, confidence intervals, exclusions and model coefficients.
- `data/modeling-appearances.csv`: complete analysis table.
- `data/heldout-appearances.csv`: 2025 board records.
- `data/toronto-velocity.csv`: qualifying pitch-type-specific appearances.
- `data/source-manifest.json`: primary source URLs and hashes.
- `data/verification.json`: source-level verification results.

Development note: the bundled local NumPy/BLAS emitted arithmetic warnings during some matrix multiplications. All predictions were finite and were checked against elementwise coefficient calculations; exported RMSEs are independently reconstructed by verify.py. No warning-generated NaNs were retained.


## Revision 2 — deeper diagnostics and an as-of pitcher dossier

The original 2025 holdout has already been reviewed. New subgroup checks are therefore **post-hoc diagnostics**, with the original model coefficients kept fixed. They are not a new untouched evaluation or a reason to tune the model against 2025.

The added evaluation slices are: inning 7+ entries with score margin within three; 0–6 MLB off-days; completed outings with at most six BF (explicitly outcome-conditioned); and equal-appearance rather than BF-weighted evaluation. The original full-sample interval remains unchanged. Additional intervals use 1,000 pitcher-cluster resamples with seed 1729, and are pointwise rather than multiplicity-adjusted. Their sample sizes and exact definitions are published in data/diagnostics.json. Frozen row predictions are in data/frozen-predictions.csv.

A fixed league-average benchmark uses the BF-weighted 2023–2024 target mean. This contextualizes how much the prior-performance/context model improves over assigning one constant value to every appearance. Neither benchmark nor diagnostic adds a newly trained model.

The new pitcher dossier is anchored to the selected appearance, not the last day in the database. Daily pitch history is truncated strictly before the selected date, includes starts and other clubs, and spans up to 42 previous dates (never earlier than the source season's March 18 start). The earlier-outcome table uses only earlier eligible relief appearances. The workload percentile is the fraction of earlier eligible appearances with seven-day workload less than or equal to the selected value; at least ten earlier appearances are required. It is a descriptive empirical rank, not a physiological norm or risk estimate.

There are 258 eligible 2025 appearances after 14+ MLB off-days. These receive an explicit missing-context flag; neither 14 days nor the 0–6 diagnostic restriction is a physiological threshold. An MLB gap can include minor-league games, rehab or other throwing.

Toronto data-quality sensitivity holds velocity baselines fixed and removes current appearances with a pitch-count discrepancy greater than two. It does not remove every potentially affected baseline observation and is not a missingness correction. The 2025 zero-off-day mean is approximately −0.142 mph in 39 appearances and −0.130 mph in the 37 retained appearances. The 2024 mean shifts from approximately −0.170 to −0.255 mph, so source disagreement is not dismissed as harmless. Both seasons are visible in the dashboard.

Review links preserve board filters, as-of date and selected appearance. They work once this exact version is hosted; localhost/file links are only local. Filtered CSV exports include observed outcomes and are explicitly for retrospective review. They should not be confused with a pre-appearance feature-only feed.
