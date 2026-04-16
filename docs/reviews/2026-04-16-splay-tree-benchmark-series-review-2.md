# Review pass 2 — splay-tree benchmark-series

## Focus
Input-shape and determinism audit.

## Findings
1. Duplicate-size handling existed implicitly, but there was no regression test proving that the CLI/helper preserves first-seen order while de-duplicating the sweep list.

## Fixes applied
- Added `test_benchmark_series_deduplicates_sizes_preserving_order` to lock in deterministic series ordering and seed assignment.

## Result
- Future refactors now have a guardrail around stable series ordering.
