# CRDT OR-Set Lab learning/self-test — 2026-04-18 — preset bundle landing + ZIP slice

## Refresh
This slice only needed a small refresh: if a generated artifact bundle is meant to be shared, every browser page inside the bundle should prefer bundle-local files over repo-relative files, otherwise the bundle looks portable but breaks when copied elsewhere.

## Self-test checklist
- re-ran `py_compile` on both the implementation and test file before regenerating artifacts
- re-ran the full unittest suite after adding bundle landing pages, bundled scripts, and ZIP packet generation
- re-ran `compare-presets --detail-output-dir ...` to regenerate the committed suite summary and all preset bundles from the CLI
- inspected the generated `concurrent-readd/index.html` to confirm it links only to bundle-local files such as `scenario-script.json`, `comparison.html`, and the ZIP packet
- listed the generated ZIP contents to confirm the archive contains the expected portable bundle files in deterministic order
- re-ran `git diff --check` after artifact regeneration

## Takeaway
A polished portfolio bundle is not just about adding more artifacts; it needs a clear landing page and local file closure. Copying the scenario script into the bundle and packaging the exact bundle directory into a ZIP makes the export much easier to share, review, and test.
