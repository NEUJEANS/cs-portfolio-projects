# Regex engine JSON benchmark suite slice research — 2026-04-19

## Brief source refresh
- Python's `json` module is enough for this slice because the workload definition is small, repo-committed, and benefits from being trivially inspectable in pull requests.
- The existing benchmark CLI already separates case execution from report rendering, which makes a file-backed suite loader a clean next step without changing the matching engine itself.
- Reproducible benchmark stories get stronger when the named workloads live in version-controlled data files instead of being hard-coded or reconstructed from shell history.

## Slice decision
Add `benchmark --suite-file` support that loads a JSON suite definition with a suite label and multiple named cases.

Why this is the right next slice:
- it turns the benchmark feature into a reusable portfolio workflow instead of a one-off demo command
- it gives reviewers a concrete workload bundle they can inspect, rerun, and extend without editing Python
- it stays bounded to CLI/data-contract work while still producing visible repo artifacts and a better interview story around reproducibility
