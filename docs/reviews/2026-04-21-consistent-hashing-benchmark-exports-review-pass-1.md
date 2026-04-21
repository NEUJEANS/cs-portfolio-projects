# 2026-04-21 consistent-hashing benchmark exports review pass 1

## Focus
Inspect the new export helpers for artifact quality and spreadsheet friendliness.

## Issue found
- The first CSV export wrote full raw floating-point precision for values like `average_load`, which made the file noisier than necessary for charting and README screenshots.

## Fix applied
- Rounded `average_load`, `imbalance_ratio`, `movement_ratio`, and `best_imbalance_ratio` to 4 decimal places in `benchmark_series_rows` before CSV serialization.

## Verification
- `python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py`
