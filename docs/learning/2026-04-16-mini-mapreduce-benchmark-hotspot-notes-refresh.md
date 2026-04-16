# Mini MapReduce benchmark hotspot notes refresh

Date: 2026-04-16

## Goal
Add concise benchmark-report narration that explains why a given synthetic dataset family should create balanced or skewed reducer behavior.

## Quick refresh
- Benchmark notes should explain the intended workload shape, not restate raw timing numbers.
- Balanced families need notes that frame reducer imbalance as partition variance rather than a designed hotspot.
- Skewed families should name the expected dominant key/status/cohort so the hottest heatmap cell has an immediate explanation.
- Keep the notes deterministic and tied to the synthetic fixture definitions already in `build_benchmark_lines()`.

## Self-test before coding
- `wordcount/skewed/logs` should mention `checkout:error` as the dominant synthetic hotspot.
- `json-group-count/skewed/incidents` should mention `triaged` as the backlog-heavy status.
- `plugin-average-score/skewed/project-week` should mention `demo-day-core` as the expected hotspot.
- Balanced families should explicitly say the dataset is intentionally even so any skew is mostly partition variance.
