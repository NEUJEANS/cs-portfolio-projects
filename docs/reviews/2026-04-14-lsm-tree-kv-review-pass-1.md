# Review pass 1: lsm-tree-kv

## Focus
API clarity and operator feedback.

## Findings
- The `delete` CLI only reported that a tombstone was written; it did not say whether the key had existed before.
- That made the command less useful for demos and harder to reason about during manual testing.

## Fixes applied
- changed `delete()` to return both the tombstone entry and an `existed` flag
- updated the CLI JSON response to include `existed_before`
- expanded tests to verify the new behavior
