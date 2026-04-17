# Review pass 3 — file-organizer custom buckets — 2026-04-17

## Focus
README/demo quality and final runnable smoke coverage.

## Findings
1. **Doc gap:** the README explained that redirected JSON output should live outside the organized directory, but it did not mention that the active config file is now auto-skipped when stored inside the target root.

## Fixes made
- documented config self-skip behavior in the README notes section
- reran a final apply + undo smoke with `buckets.json` inside the target directory and reports/manifests written outside it

## Verification
- `npm test --prefix projects/file-organizer-cli`
- final smoke: organize + undo apply flow with config-inside-root safety proof
