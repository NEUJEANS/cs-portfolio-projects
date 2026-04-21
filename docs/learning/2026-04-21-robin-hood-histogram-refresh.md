# 2026-04-21 Robin Hood histogram refresh + self-tests

## Quick refresh
- Python `dict` aggregation is enough for deterministic histogram buckets; no external charting/statistics dependency is needed.
- For machine-readable CSV exports, nested histogram objects should be JSON-encoded into a single field instead of relying on Python repr output.
- If histogram bucket keys are stringified for JSON, preserve insertion order instead of re-sorting lexicographically so probe distance `10` does not appear before `2`.
- When aggregating deterministic trial histograms, pooled probe-distance standard deviation should be recomputed from the merged bucket counts instead of averaging per-trial stddev values.
- Reusing one static HTML metric-bar helper keeps the dashboard lightweight while still making bucket proportions visually obvious.

## Self-tests used in this slice
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v`
- benchmark smoke run writing Markdown, HTML, CSV, and JSON outputs and checking that each includes `probe_distance_histogram`
