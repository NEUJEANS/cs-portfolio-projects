# Refresh / self-test — 2026-04-23 — log-analyzer facet gallery/detail PNG exports

## Quick refresh
- Reuse the existing facet-ranking gallery HTML and detail-bundle HTML pages as the raster source so screenshot exports cannot drift from the shipped browser artifacts.
- Keep screenshot capture on the shared Chrome helper path introduced for card PNGs instead of creating gallery-only or bundle-only browser code.
- When bundle PNGs are enabled, make the manifest, index links, and ZIP packet include the screenshot files deterministically so handoff bundles stay self-describing and reproducible.

## Self-test plan
1. Wire gallery PNG and bundle PNG flags into the existing HTML export path, including validation for required companion flags.
2. Extend tests for CLI success, manifest/ZIP contents, and missing-flag validation, using real Chrome-backed PNG capture when available.
3. Regenerate the committed gallery and detail-bundle artifacts from `docs/artifacts/log-analyzer/facet-ranking-sample.log`, then verify the PNG files exist and are linked from the HTML/manifest outputs.
4. Finish with `py_compile`, full `unittest`, real CLI smoke runs, and three focused review passes.
