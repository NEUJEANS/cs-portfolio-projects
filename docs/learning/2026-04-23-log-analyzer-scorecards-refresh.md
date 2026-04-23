# Refresh / self-test — 2026-04-23 — log-analyzer facet gallery/detail scorecards

## Quick refresh
- Reuse the grouped facet-ranking rows that already back the gallery and detail bundle; do not introduce a second analysis path just to build overview tiles.
- Prefer compact responsive card grids so the same HTML works for browser viewing and the committed PNG snapshots.
- Keep the quick-read layer in the bundle manifest too, so resumability and downstream tooling can inspect the same highlights without scraping HTML.

## Self-test plan
1. Add derived scorecard highlights per facet slice from the strongest existing ranking rows.
2. Render those highlights in gallery cards and the detail-bundle index, and thread them into the manifest.
3. Extend tests for gallery HTML and bundle manifest/index output.
4. Rebuild the committed artifacts, then finish with `py_compile`, full `unittest`, smoke checks, and three review passes.
