# Review pass 1 - API and correctness

## Focus
- inspect the new concurrent snapshot API for correctness and backward compatibility

## Findings
1. Duplicate snapshot IDs in CLI input would have been silently overwritten by `dict(...)` construction.
2. Scoped marker delays could reference a snapshot ID that was never declared.

## Fixes applied
- added `parse_snapshot_specs()` to reject duplicate snapshot IDs explicitly
- added concurrent CLI validation so `--marker-delay snapshot_id:...` must reference a declared snapshot
- added tests for both validation paths

## Result
- single-snapshot flow remains unchanged
- concurrent mode now fails fast on ambiguous or mismatched input
