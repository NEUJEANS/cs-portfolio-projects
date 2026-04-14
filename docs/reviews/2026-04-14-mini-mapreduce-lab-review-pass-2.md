# mini-mapreduce-lab review pass 2

## Focus
API and validation edge cases.

## Findings
1. CLI validation rejected `--reducers 0`, but the programmatic `execute_job()` path did not explicitly guard invalid reducer counts before reduction.

## Fixes applied
- Added reducer-count validation inside `reduce_shards()`.
- Added `test_programmatic_api_rejects_non_positive_reducers`.
