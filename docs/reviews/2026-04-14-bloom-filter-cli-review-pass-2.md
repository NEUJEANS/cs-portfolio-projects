# Bloom Filter CLI Review Pass 2

## Focus
CLI ergonomics and failure paths.

## Issues found
1. `remove` on a standard Bloom filter would have produced a Python traceback instead of a clean CLI error.
2. The CLI surface did not include dedicated commands for creating or mutating counting filters.

## Fixes applied
- Added `build-counting` and `remove` subcommands for a full counting-filter workflow.
- Updated `main()` to convert `ValueError` and `OverflowError` into clean CLI exit messages.
- Added CLI tests covering counting build/remove/stats flows and the standard-filter rejection case.
