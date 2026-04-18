# CRDT OR-Set Lab — comparison preset-suite review log (2026-04-18)

## Review pass 1 — code path / CLI ergonomics
- Reviewed the new preset registry, suite builder, and CLI wiring for `list-presets` / `compare-presets`.
- Found one issue during review: an unknown preset name raised a raw Python traceback.
- Fixed it by routing `ValueError` through `argparse` so the CLI now returns a concise usage error instead.
- Added a regression test that asserts the error path mentions the unknown preset without printing a traceback.
- Result: preset discovery/selection is safer for demo use and classroom typo recovery.

## Review pass 2 — docs / artifact consistency
- Regenerated the committed preset-suite Markdown/HTML/JSON artifacts after the CLI fix.
- Verified README and both checklist files mention the new built-in preset suite and its artifact outputs.
- Confirmed the new preset scripts are referenced project-relatively (`sample_compare_ops.json`, `presets/unobserved-remove.json`, `presets/observed-remove-sync.json`) so the artifacts stay portable on GitHub.
- Result: the implementation, committed artifacts, and docs now tell the same story.

## Review pass 3 — real CLI smoke / browser artifact spot-check
- Ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py list-presets --json` and confirmed all three shipped presets appear with the expected script paths.
- Ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out ... --suite-html-out ... --suite-json-out ...` and confirmed the suite reports 2 divergent cases plus 1 aligned control case.
- Served the repo locally and opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/comparison-presets.html` to verify the gallery renders the three scenario cards and the divergence/alignment summary in a real browser.
- Result: the preset suite works end-to-end for CLI generation plus browser-viewable portfolio output.
