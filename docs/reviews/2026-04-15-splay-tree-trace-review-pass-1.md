# Review pass 1 - splay-tree trace + DOT

## Focus
Correctness of the new tracing API and whether the access summary stayed backward compatible.

## Findings
- `access_sequence()` should keep its old shape so earlier consumers do not suddenly receive verbose step data.
- The new traced variant should capture incremental rotations/comparisons per key rather than only totals.

## Fixes applied
- Kept `access_sequence()` as a compatibility wrapper.
- Added `trace_access_sequence()` as the verbose API and tested per-step metrics.
