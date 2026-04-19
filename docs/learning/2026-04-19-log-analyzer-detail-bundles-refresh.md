# Refresh / self-test — 2026-04-19 — log-analyzer facet detail bundles

## Quick refresh
- Reuse the existing grouped facet-ranking data so gallery pages, focused slice pages, CSV exports, and the bundle manifest all describe the same run.
- Keep all links portable by resolving local targets relative to the output file being written (`index.html` vs `slices/<card-id>.html`).
- Deterministic ZIP output needs fixed member order plus fixed metadata, not just stable file contents.

## Self-test plan
1. Add bundle generation helpers that write the index, manifest, per-slice pages, and ZIP packet from one analyzed result.
2. Cover direct bundle generation in tests, including relative back-links to the gallery and deterministic ZIP bytes across reruns.
3. Add CLI coverage for a successful bundle export and for the expected validation error when `--facet-ranking-detail-bundle-dir` is used without `--facet-field`.
4. Regenerate the committed sample artifact bundle and inspect the manifest/ZIP contents before the review passes.