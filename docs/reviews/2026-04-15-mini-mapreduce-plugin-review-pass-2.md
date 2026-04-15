# mini-mapreduce plugin review pass 2

## Focus
Failure modes and API validation.

## Findings
1. Dynamic loading needs explicit contract checks or runtime errors become opaque.
2. Plugin jobs should fail early when `--plugin` is missing instead of falling into a generic unsupported path.

## Fixes applied
- Kept loader validation for missing or non-callable `map_records`, optional `combine_values`, and required `reduce_key` hooks.
- Added CLI coverage for missing `--plugin` and project/repo tests for malformed plugin files.
