# 2026-04-15 Cuckoo hashing lab review pass 2

## Focus
Snapshot validation and resumability safety.

## Issue found
- `from_dict()` trusted snapshot entry lists too much, so duplicate keys or empty keys could be loaded silently and create confusing demo state.

## Fix
- Added snapshot validation for minimum capacity, empty keys, and duplicate keys before placement.
- Added regression tests that reject malformed duplicate-key snapshots.

## Result
- Saved tables are now safer to reload and easier to trust during portfolio demos.
