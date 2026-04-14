# Review pass 1 — bloom-filter-cli

## Focus
Core implementation correctness and persistence.

## Findings
1. `save_filter` did not create parent directories, so writing to a nested output path could fail.

## Fixes applied
- Added `path.parent.mkdir(parents=True, exist_ok=True)` before writing the serialized JSON file.

## Verification
- `python3 -m unittest projects/bloom-filter-cli/test_bloom_filter.py`
