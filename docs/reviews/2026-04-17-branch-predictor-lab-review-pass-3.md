# Branch-predictor-lab review — pass 3

## Focus
Resumability and portfolio-level discoverability.

## Issue found
- The new project existed locally, but the repo-level progress tracking was not yet updated. Without that bookkeeping, the next automation run could miss the slice or treat the repository state as incomplete.

## Fix applied
- Added `branch-predictor-lab` to the root `README.md` progress list.
- Added the architecture-coverage note to `docs/checklists/master_checklist.md`.
- Kept both project-level and docs-level checklist files aligned.

## Result
- The slice is now discoverable from the repo root and resumable for future cron runs.
