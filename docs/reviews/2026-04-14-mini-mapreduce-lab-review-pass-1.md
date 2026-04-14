# mini-mapreduce-lab review pass 1

## Focus
Implementation correctness for the new reducer partitioning slice.

## Findings
1. The first draft added reducer stats but lacked a regression test proving aggregate output stays the same when reducer count changes.

## Fixes applied
- Added `test_reducer_count_changes_bucket_stats_not_aggregate_output` to lock in the key MapReduce invariant.
