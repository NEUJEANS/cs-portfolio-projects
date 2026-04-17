# Review pass 2 — file-organizer custom buckets — 2026-04-17

## Focus
CLI validation coverage and flag-combination regressions.

## Findings
1. **Coverage gap:** after adding `--config`, the updated arg-parsing tests no longer explicitly protected the older `--undo --manifest-out` rejection path.

## Fixes made
- restored explicit regression coverage for `--undo --manifest-out`
- reran the full Node test suite after the parser-test update

## Verification
- `npm test --prefix projects/file-organizer-cli`
