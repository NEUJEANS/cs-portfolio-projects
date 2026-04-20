# Two-phase commit lab research — 2026-04-20 — tag-filtered catalogs

## Why no external web research this slice
- This slice does not change 2PC protocol semantics or recovery behavior.
- The work stays inside the existing artifact-generation pipeline: scenario-tag normalization, catalog rendering, and filesystem-safe output naming.

## Internal references reviewed
- `projects/two-phase-commit-lab/two_phase_commit_lab.py`
  - existing tag normalization, catalog rendering, incident dashboard writing, and CLI argument handling
- `projects/two-phase-commit-lab/*.json`
  - current tag distribution across the committed seven-scenario bundle
- `docs/artifacts/two-phase-commit-lab/`
  - current catalog/dashboard/report naming so filtered outputs do not overwrite the main bundle

## Slice decision
- Reuse the existing scenario-tag normalization rules for CLI filters so author-facing tags and user-facing filter flags stay consistent.
- Support repeatable `--include-tag` filters with default any-match behavior plus an explicit all-tags mode for narrower subsets.
- Write filtered incident dashboards to a catalog-stem-specific filename unless the target is the canonical `scenario_catalog.md`, which preserves the existing main-bundle path.
