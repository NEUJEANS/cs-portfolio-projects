# Two-phase commit lab learning note — 2026-04-20 — tag-filtered catalogs

## Quick refresh / self-test
- Existing scenario tags already normalize to lowercase kebab-case; CLI tag filters should use the same normalization helper rather than inventing a second code path.
- Filtered bundle artifacts need their own incident dashboard filename, otherwise generating a subset catalog in the same directory can silently overwrite the main dashboard.
- A useful subset should still link to the same per-scenario reports and companion compare/termination artifacts, so filtering should happen before entry generation rather than by stripping rows after render.

## Resulting implementation rule
- Filter scenario paths first, then build catalog entries and write artifacts only for the selected subset.
