# Review pass 3 — file-organizer preset helpers — 2026-04-17

## Focus
README/demo clarity and final runnable preset smoke coverage.

## Findings
1. **Doc gap:** the README explained how to export a preset JSON file, but it did not show the simpler direct `--preset` quick-start path before the shared-config workflow.

## Fixes made
- added a direct `node organizer.js ~/Downloads --preset coursework --recursive` quick-start example ahead of the export/reuse walkthrough
- reran a final smoke flow covering direct preset organize + undo plus exported-preset reuse through `--config`

## Verification
- `npm test --prefix projects/file-organizer-cli`
- final smoke: direct `--preset coursework` organize + undo, then `--write-preset frontend-assets` and reuse via `--config`
