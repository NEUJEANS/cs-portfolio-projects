# Review pass 1 - segment tree range-set slice

## Checks
- Ran the targeted unittest suite for `projects/segment-tree-range-query-lab`.
- Verified the new sample flow now exercises both `range-add` and `range-set`.

## Issue found
- The new sample expectation in `test_sample_json_shape` was off by 3 because the post-assignment window still includes the unchanged trailing `9`.

## Fix applied
- Corrected the expected `after_range_set` sum from `30` to `33`.
