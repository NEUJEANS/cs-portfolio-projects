# Wrap-up — 2026-04-20T20:13:00Z — tarjan-scc-lab PNG capture

## What changed
- added first-class `--png-output` support to `compare` so the Tarjan vs. Kosaraju HTML dashboard can emit a slide-ready PNG in the same run
- resolved Chrome/Chromium automatically (with optional `--chrome-binary`) and captured the dashboard through a deterministic headless command path with viewport and wait-budget knobs
- auto-sized the PNG viewport height from trial/component counts while still allowing explicit `--png-width`, `--png-height`, and `--png-capture-ms` overrides
- linked the new PNG companion from the generated HTML dashboard and refreshed the committed sample compare bundle under `docs/artifacts/tarjan-scc-lab/`
- refreshed the project README plus slice checklist, research note, self-test note, and 3-pass review log so the slice is resumable

## Tests and reviews run
- review log: `docs/reviews/2026-04-20-tarjan-scc-png-capture-review.md`
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --json-output /tmp/tarjan-png-slice/benchmark.json --csv-output /tmp/tarjan-png-slice/benchmark.csv --markdown-output /tmp/tarjan-png-slice/benchmark.md --html-output /tmp/tarjan-png-slice/benchmark.html --png-output /tmp/tarjan-png-slice/benchmark.png >/tmp/tarjan-png-slice/stdout.json`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 5 --json-output docs/artifacts/tarjan-scc-lab/sample-compare.json --csv-output docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output docs/artifacts/tarjan-scc-lab/sample-compare.md --html-output docs/artifacts/tarjan-scc-lab/sample-compare.html --png-output docs/artifacts/tarjan-scc-lab/sample-compare.png >/tmp/tarjan-sample-png-stdout.json`
- `file docs/artifacts/tarjan-scc-lab/sample-compare.png`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- feature commit: `f9d6c684d45b1d2c2095fa73583d7619bd305704`

## Next step
- add a small Tarjan SCC showcase landing page that links the SCC explanation, condensation artifacts, and benchmark bundle so the project reads as one polished portfolio story
