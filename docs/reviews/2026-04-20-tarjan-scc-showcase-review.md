# Tarjan SCC showcase review — 2026-04-20

## Pass 1 — benchmark snapshot consistency audit
- Re-read the new `showcase-demo` flow while diffing the committed `sample-showcase.md` against `sample-compare.json`.
- Issue found: the landing page recomputed a fresh benchmark snapshot even when a linked benchmark JSON artifact was supplied, so the showcase averages could drift away from the linked compare bundle.
- Fix applied: `showcase-demo` now reuses `--compare-json-path` as the source of truth for the embedded benchmark snapshot whenever that artifact is supplied.

## Pass 2 — malformed linked-benchmark guardrail audit
- Reviewed the new linked-benchmark loading path for bad or partially edited artifact files.
- Issue found: the first JSON-reuse patch trusted `repeat`, `component_count`, and `average_ms` values without normalizing them, which could have produced formatting crashes or misleading output if the artifact was malformed.
- Fix applied: added `load_compare_artifact_payload()` validation/normalization plus focused CLI tests for invalid JSON and bad numeric fields.

## Pass 3 — docs + committed artifact audit
- Re-ran the committed compare/explain/condensation/showcase artifact bundle and checked the README workflow copy against the updated behavior.
- Issue found: the first README/showcase revision did not explicitly say that `showcase-demo` reuses the linked benchmark JSON, leaving the consistency guarantee implicit.
- Fix applied: documented the reuse behavior in `projects/tarjan-scc-lab/README.md` and regenerated the sample showcase bundle so the published landing page now matches the committed benchmark JSON exactly.

## Final verification
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 5 --json-output docs/artifacts/tarjan-scc-lab/sample-compare.json --csv-output docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output docs/artifacts/tarjan-scc-lab/sample-compare.md --html-output docs/artifacts/tarjan-scc-lab/sample-compare.html --png-output docs/artifacts/tarjan-scc-lab/sample-compare.png >/tmp/tarjan-showcase-compare-stdout.json`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json explain --limit 4 > docs/artifacts/tarjan-scc-lab/sample-explain.txt`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json condensation > docs/artifacts/tarjan-scc-lab/sample-condensation.json`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json dot > docs/artifacts/tarjan-scc-lab/sample-condensation.dot`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json mermaid > docs/artifacts/tarjan-scc-lab/sample-condensation.mmd`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json showcase-demo --repeat 5 --limit 4 --markdown-output docs/artifacts/tarjan-scc-lab/sample-showcase.md --html-output docs/artifacts/tarjan-scc-lab/sample-showcase.html --explain-path docs/artifacts/tarjan-scc-lab/sample-explain.txt --condensation-json-path docs/artifacts/tarjan-scc-lab/sample-condensation.json --dot-path docs/artifacts/tarjan-scc-lab/sample-condensation.dot --mermaid-path docs/artifacts/tarjan-scc-lab/sample-condensation.mmd --compare-json-path docs/artifacts/tarjan-scc-lab/sample-compare.json --compare-csv-path docs/artifacts/tarjan-scc-lab/sample-compare.csv --compare-markdown-path docs/artifacts/tarjan-scc-lab/sample-compare.md --compare-html-path docs/artifacts/tarjan-scc-lab/sample-compare.html --compare-png-path docs/artifacts/tarjan-scc-lab/sample-compare.png >/tmp/tarjan-showcase-stdout.json`
- `git diff --check`
- inline consistency check: confirmed the committed showcase Markdown/HTML embed the exact average timings from `docs/artifacts/tarjan-scc-lab/sample-compare.json`
