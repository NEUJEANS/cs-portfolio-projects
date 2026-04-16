# Review pass 1 - benchmark CSV compatibility

## Focus
- inspect the new benchmark-series implementation for regression risk in the existing single-run benchmark flow
- verify artifact shape stability for `benchmark --csv-file`

## Findings
1. The first draft reused series rows for the single-size `benchmark` command, which would have added a new `series_count` column to the existing `artifacts/red-black-vs-avl.csv` format.

## Fixes applied
- restored the original single-run benchmark CSV shape by keeping `series_count` only in `benchmark-series` output
- regenerated both benchmark artifacts after the fix

## Result
- existing single-benchmark consumers keep the old flat CSV schema
- the new multi-size workflow still emits richer series rows for charting
