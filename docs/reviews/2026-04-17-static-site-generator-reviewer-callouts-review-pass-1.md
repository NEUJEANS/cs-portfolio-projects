# Static-site-generator reviewer callouts review — pass 1

## Focus
Author-facing docs and checklist accuracy for the new callout syntax.

## Issue found
- The first implementation added reviewer/architecture callout rendering, but README/checklist docs still described this as a future improvement, which would make the feature easy to miss and leave the project status inconsistent.

## Fix applied
- Updated `projects/static-site-generator/README.md` with the new `[!REVIEWER]` / `[!ARCHITECTURE]` workflow, supported marker list, and refreshed future-improvement note.
- Marked the project checklist item complete and queued a new follow-up slice.
- Added the new slice entry to `docs/checklists/static-site-generator.md`.

## Result
- The implementation, README, and checklists now describe the same current feature set.
