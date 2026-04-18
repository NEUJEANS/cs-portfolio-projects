# CRDT OR-Set Lab — preset bundle landing + ZIP review log (2026-04-18)

## Review pass 1 — bundle landing page data model
- Reviewed the new preset-bundle landing page renderer against the existing `build_semantics_comparison(...)` output.
- Issue found: the first draft expected an `outcome` field that does not exist on raw comparison payloads used during detail-bundle generation.
- Fix applied: derive `align` vs `diverge` directly from `final_divergence` inside the landing-page renderer.
- Result: per-preset landing pages now work for the actual detail-generation code path instead of only the suite-summary shape.

## Review pass 2 — self-contained bundle links
- Reviewed the generated preset HTML artifacts for portability instead of only checking that the new bundle files existed.
- Issue found: the bundle pages still linked scenario scripts back to repo-level paths, which weakened the goal of a self-contained packet.
- Fix applied: added bundled `scenario-script.json` copies inside each preset directory and rewired timeline / replay / anti-entropy / comparison pages to link to the bundled copy.
- Result: each preset directory can now stand on its own as a shareable static packet.

## Review pass 3 — suite discoverability / archive verification
- Reviewed the suite-level Markdown/HTML summaries and the generated ZIP packet contents after the bundle-local links were fixed.
- Issue found: the suite outputs still treated the comparison page as the first-class link, which hid the new landing page / ZIP packet affordance and made the shareable packet easy to miss.
- Fix applied: surfaced bundle + ZIP links ahead of the existing per-artifact links in the suite renderers, extended tests to cover the new keys, and asserted the ZIP member list explicitly.
- Result: the suite summary now advertises the new shareable entry points, and archive contents are regression-tested.

## Final verification
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py projects/crdt-orset-lab/test_crdt_orset_lab.py`.
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`35/35` passing).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py compare-presets --suite-markdown-out docs/artifacts/crdt-orset-lab/comparison-presets.md --suite-html-out docs/artifacts/crdt-orset-lab/comparison-presets.html --suite-json-out docs/artifacts/crdt-orset-lab/comparison-presets.json --detail-output-dir docs/artifacts/crdt-orset-lab/comparison-presets`.
- Listed `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/concurrent-readd-bundle.zip` and confirmed it contains the landing page, bundled scenario script, HTML artifacts, Markdown companions, and JSON outputs.
- Re-ran `git diff --check`.
