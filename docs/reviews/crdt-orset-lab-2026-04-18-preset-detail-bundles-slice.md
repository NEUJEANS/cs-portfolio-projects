# CRDT OR-Set Lab — preset detail-bundles review log (2026-04-18)

## Review pass 1 — code path / relative-link wiring
- Reviewed the new helper path functions, detail-bundle generation flow, and `compare-presets --detail-output-dir` CLI wiring.
- Verified the suite outputs are enriched via data (`detail_bundle`) instead of ad-hoc string concatenation in multiple renderers.
- Result: the export path stays centralized enough to extend without breaking existing summary-only behavior.

## Review pass 2 — docs / artifact consistency
- Found one issue during review: the README still documented only the suite summary outputs and did not mention `--detail-output-dir` or the new committed bundle directory.
- Fixed the README command example, feature description, and committed-artifact examples so the docs match the generated outputs.
- Result: repo docs and committed artifacts now describe the same workflow.

## Review pass 3 — real CLI smoke / browser artifact spot-check
- Ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out docs/artifacts/crdt-orset-lab/comparison-presets.md --suite-html-out docs/artifacts/crdt-orset-lab/comparison-presets.html --suite-json-out docs/artifacts/crdt-orset-lab/comparison-presets.json --detail-output-dir docs/artifacts/crdt-orset-lab/comparison-presets` and confirmed the suite writes linked per-preset bundles.
- Served the repo locally and opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/comparison-presets.html`, then followed the `Comparison` link for `concurrent-readd` to confirm the relative detail-page navigation works in a real browser.
- Result: the preset suite works end-to-end for generation plus clickable browser navigation into a preset-specific bundle.
