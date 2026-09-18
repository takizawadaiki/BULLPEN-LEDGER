# Bullpen Ledger — research brief

**Question:** Does recorded recent workload improve the prediction of a reliever’s next appearance once prior performance and entry conditions are known?

**Decision:** The tested public-data model does not justify a fatigue ranking or an availability recommendation. The workload log is useful as an auditable review surface; the predictive layer has not earned operational use.

## Evidence

The analysis uses 38,925 eligible regular-season relief appearances from Retrosheet, spanning 2023–2025. Model development uses 25,844 appearances from 2023–2024; evaluation uses 13,081 from 2025. The primary target is strikeouts minus unintentional walks per batter faced. It is a noisy performance proxy, not a physiological fatigue measure.

Adding rest categories and recent pitch-count features changed held-out weighted RMSE from 26.474 to 26.480 percentage points. The paired pitcher-bootstrap interval for that change includes zero. The observed change is too small and uncertain to support an operational claim.

A separate Toronto Statcast analysis keeps pitch type fixed at four-seam fastballs. It compares each outing with up to five earlier qualifying Toronto relief outings, without using future appearances. In 2025, the zero-MLB-off-day group averaged a 0.142 mph decline, but its 95% interval spans roughly −0.357 to +0.161 mph. There are only 39 appearances from eight pitchers in that stratum. This is a hypothesis-generating signal, not proof of a rest effect.

## What makes this useful to baseball operations

1. **The clock is correct.** Historical workload comes from prior dates. Trade history and starts contribute to workload. Suspended-game continuation dates are handled through dated plays; ambiguous same-day appearances are excluded as outcomes.
2. **The benchmark is explicit.** Workload must beat a model with prior performance and context. A statistically interesting association is not automatically a useful forecast.
3. **Uncertainty changes the recommendation.** The dashboard exposes intervals and sample sizes. It does not turn a few pitches or a small velocity decline into a medical label.
4. **The output is inspectable.** A reviewer can click an actual appearance, inspect the seven-day pitch history, reveal the outcome, download the modeling rows, and reproduce the pipeline.
5. **The data boundary is visible.** Days without MLB pitching may include minor-league appearances, rehab or bullpen sessions. They are not confirmed rest days.

## The biggest threat to interpretation

Deployment is selected. Managers may already avoid using tired pitchers; the observed zero-rest group may be unusually healthy or trusted. A weak observed workload association can coexist with a real fatigue effect. This study does not observe counterfactual performance among pitchers who were rested.

Other limitations include omitted opponent quality, handedness, exact recovery hours, travel, warm-ups and pitch-shape measures. A full-season role filter defines a retrospective pitcher cohort. This is not a model for classifying unknown players in real time. The Toronto velocity sample is small and exploratory.

## A five-minute walkthrough

- **First minute:** Explain the decision and why predicting a next appearance is harder than plotting ERA against days off.
- **Second minute:** Open Toronto in the historical board. Select “Pitched both prior days.” Explain the underlying pitch counts and why this is a workload flag, not a fatigue diagnosis. Reveal the outcome only after describing what was knowable beforehand.
- **Third minute:** Show the held-out comparison. Explain why reporting no clear gain is the right conclusion, and why it does not imply fatigue is irrelevant.
- **Fourth minute:** Show the four-seam panel. Discuss a pitcher-specific, trailing baseline; pitch-type consistency; sample-size limitations; and why confidence intervals matter.
- **Fifth minute:** Show the reproduction files and propose the next experiment: collect warm-up and recovery data, model the deployment process, and validate on a new period with opponent-adjusted, pitch-level targets.

## Questions to be ready for

**Why not ERA?** Short relief appearances produce unstable ERA, and sequencing/inherited-run accounting complicates it. K−uBB is also noisy and incomplete; it was chosen as a transparent, batter-level-denominator proxy, not a full measure of pitching value.

**Why is a null result worth showing?** It prevents deploying an unsupported score. The useful research output is the tested boundary of the data and a concrete plan for improving information and identification.

**Would you recommend resting a specific pitcher?** Not from this study alone. I would bring the recorded workload and its missing context to staff, not substitute it for recovery information or coaching judgment.

**How would you improve it?** Add exact throwing exposure, roster/availability information, opponent quality, handedness, pitch shape, exact elapsed recovery time and travel. Use hierarchical pitcher-level estimates and a new chronological validation period. The already examined 2025 season is no longer a fresh holdout for a redesigned model.

**What should you avoid claiming?** That workload causes the estimated changes; that the model detects injury risk; that a pitcher is safe or unsafe to use; that this is an official club tool; or that a null result rules out fatigue.

Before presenting, run a few appearances yourself and explain each feature and calculation in your own words. Describe the use of coding or analytical assistance accurately if asked.

Sources and full methods: [README](README.md), [Retrosheet](https://www.retrosheet.org/downloads/csvdownloads.html), [Baseball Savant documentation](https://baseballsavant.mlb.com/csv-docs). Exact computed results: [summary](data/summary.json), [Toronto supplement](data/toronto.json).


## Revision 2: a stronger demonstration

Start by selecting Brendon Little and a historical appearance. Use the dossier to explain which pitches occurred before that date, how the seven-day total compares with his own earlier eligible outings, and what remains unobserved. A relative workload rank is not a probability of fatigue.

Then open “Does the conclusion travel?” Explain that the models remain frozen and the new slices are post-hoc. The incremental-workload intervals span zero in the late/close, no-long-gap, short-outing and equal-weight checks. Contrast that with the context model's improvement over a single league-average prediction. This isolates the research question: prior performance/context has some value, but these added workload features have not shown a clear benefit for this target and model.

Finally, demonstrate the as-of-date control, a link that restores the selected record, and a filtered CSV export. This makes the work easy for another analyst to audit and discuss. Use the Toronto feed-agreement sensitivity to show that data-source discrepancies were measured, not silently ignored.
