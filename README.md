# Home by Construction

Auditing Coverage-Dependent Origin Labels in Street-Art Data

Research manuscript prepared for ACM FAccT 2027. This is original analysis of a new six-country Street Art Cities panel using a published measurement rule. It is **not** a reproduction of WIPO's historical 37-country estimates. It has not been accepted or peer reviewed. Submission status is recorded separately.

## What was actually run

- Six publicly linked October 2026 country CSVs: 48,690 raw markers.
- Four linked September CSVs for the monthly replay.
- Primary single-artist population: 42,730 records, 12,373 artist URLs.
- Qualifying cohort: 3,051 artists and 30,696 records; 94.1% fall in their geography-derived anchor country.
- Conservative nationality comparator: 196/933 artist mismatches, including 172 tagged outside the panel. Tags are not verified ground truth.
- All 63 nonempty country supports; every identified collector deletion per qualifying artist; 200 matched random-deletion replicates.
- Exact fixed-cohort country completion envelopes and all 15 joint destination-pair reversal minima. The smallest minimum is 14 additions (Portugal–Belgium); the largest is 352 (Netherlands–Spain).
- Monthly replay: no resolved anchor switches; seven formerly assigned artists become unassigned.
- Seven unit tests, including exhaustive target and abstention cost checks; independent full-panel counts and 16 certified optimal MILP comparisons.

The completion model represents possible additional documentation, not observed missing production. No records were inserted into the source platform. Extrema for different pairs are separate scenarios. The contributions are the concrete empirical audit, shared-artist sensitivity accounting, and a reporting discipline, not a new generic optimization algorithm or verified nationality classifier.

## Reproduce

Python 3.9.6 was used. Exact package versions are in `environment.json` and `requirements.txt`. Install them in an isolated environment. Tectonic is needed only to build the manuscripts.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/fetch_data.py data
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python src/analyze.py data
.venv/bin/python src/rankings.py data
.venv/bin/python src/validate.py data
.venv/bin/python src/figures.py
cd paper
tectonic -X compile manuscript.tex
tectonic -X compile author.tex
```

Fetch verifies every source against its frozen SHA-256, failing on changed data. Raw exports are deliberately absent from this repository; retrieve them from the data owner subject to its conditions. If these URLs are later unavailable, obtain the exact files from the source rather than substitute current exports. The saved hashes do not themselves guarantee perpetual source availability.

`results/` contains aggregate and anonymous numerical diagnostics. `PROTOCOL.md` is a local dated plan created after schema inspection and before outcome computation; it is not an external preregistration. The nationality parser uses the released finite alias dictionary and abstains on unresolved identity terms.

## Data-agnostic reporting routine

`src/audit_contract.py` accepts country counts and optional independently supplied biographical evidence. It preserves the latter separately, labels the geography output as a documented anchor, and calculates minimum additions for both reassignment and abstention. It asserts budget stability only below both costs. It never infers biography from the counts.

```sh
python src/audit_contract.py examples/illustrative_counts.json --budget 1
```

The example is an expressly synthetic small arithmetic case, not an artist observation. It illustrates a weak-majority anchor that can become unresolved after one added record. The source tests verify this behaviour.

## Interpretation and rights

See `RESEARCH_NOTES.md` for related-work distinctions, prior-paper overlap screening, commercial context, and limitations. The source code is MIT licensed. The manuscript is © 2026 Shivam Gupta; redistribution rights to the source dataset, imagery, and profiles are not conveyed. The source site's academic-use and non-academic integration restrictions apply. No artist/hunter identities, coordinates, addresses, images, or raw data are redistributed.

The anonymous manuscript and artifact must be used for review. An identifying GitHub URL must not be placed in the FAccT submission. Authorship, conflicts, reviewing experience, and any final integrity declarations require truthful author information; the repository cannot establish those personal facts.
