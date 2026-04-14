# Review pass 3 — bloom-filter-cli

## Focus
Docs, packaging, and smoke-test usability.

## Findings
1. README usage referenced an input file but the project did not include one.

## Fixes applied
- Added `sample_items.txt` to make the build command runnable immediately.
- Updated README to point to the sample input file.

## Verification
- `python3 -m py_compile projects/bloom-filter-cli/bloom_filter.py`
- full build/check/stats smoke test against `sample_items.txt`
