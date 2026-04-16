# Review pass 1 — consistent-hashing virtual-node benchmark

## Focus
CLI safety and benchmark input validation.

## Findings
1. `benchmark` and `remap` relied on deeper runtime validation for topology changes, which would surface as a later `ValueError` instead of a clear CLI-level argument error.

## Fixes
- Added mutually exclusive `--add-node` / `--remove-node` argparse groups for both `remap` and `benchmark`.
- Added a CLI regression test that verifies conflicting benchmark topology-change flags are rejected cleanly.
