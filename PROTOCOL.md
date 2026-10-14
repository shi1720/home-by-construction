# Analysis protocol, 14 October 2026

This is a timestamped local analysis plan, not an independently preregistered study.
The data schema and country sizes were inspected before this plan; outcome analyses had not run.

Question: How do documentation support and contributor concentration affect geography-derived artist anchors and destination-level international-activity indicators?

Population: All six October 2026 CSV exports linked on the public Street Art Cities open-data page at retrieval (BE, DE, ES, NL, PT, US). No inaccessible country export will be imputed. Primary unit is a marker with exactly one declared artist and a nonempty artist URL. Artist URLs define identity. All statuses are included; active-only is sensitivity. Unique marker IDs required. The historical WIPO export is unavailable without request; this is an audit of the published measurement rule on a new panel, not reproduction of its numerical estimates.

Anchor: At least three documented markers, unique most represented country, at least half the artist's markers in that country. Ties abstain. Do not call anchors nationality or birthplace.

Primary analyses:
1. Country support: all 63 nonempty subsets; compare labels on artists assigned in the full panel, separating reassignment, abstention, and disappearance.
2. Collector support: delete each represented hunter's records per artist, retaining the original evaluation cohort; separate reassignment and abstention. Compare deletion of the artist's largest hunter against uniformly sampled marker deletions of the same size (200 deterministic random seeds).
3. Completion sensitivity: exact minimum number of additional documented works required to assign any country, including one outside the panel. Compute sharp fixed-cohort destination-share extrema under total addition budgets 0, 1%, 5%, 10%, 20%, 50% of cohort size using 0-1 knapsack. These are conditional sensitivity bounds, not population confidence intervals or estimates of missingness.
4. Metadata: compare anchors with unambiguous singleton nationality tags on single-artist markers. Normalize a documented finite alias dictionary; abstain on unknown and multiple values. Artist-level consistency required. Tags are an unverified comparator, not ground truth.
5. Longitudinal replay: BE, ES, NL, PT September-October snapshots only; distinguish new marker documentation from retagging of unchanged marker IDs. No artwork creation or migration inference from upload dates.

Sensitivity: active-only; strict majority; at least 10 markers; all recorded artist links with each marker-artist pair counted once (not an artwork-weighted statistic).

Validation: exhaustive small-state verification of the addition-cost formula; exhaustive knapsack checks; independent Counter-based anchor implementation; integrity and fixed-denominator checks. Results are finite-panel descriptive statistics; no p-values that presume probability sampling.
