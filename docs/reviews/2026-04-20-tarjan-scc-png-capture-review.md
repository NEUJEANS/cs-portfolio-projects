# Tarjan SCC PNG capture review — 2026-04-20

## Pass 1 — Chrome command/path audit
- Re-read the new PNG helper while checking how artifact paths behave when the CLI is run from nested directories such as `projects/tarjan-scc-lab/`.
- Issue found: the first draft passed the PNG output path through to Chrome without resolving it, which made the screenshot destination depend on the caller's current working directory.
- Fix applied: `build_compare_png_command()` now resolves both the HTML input and PNG output paths before invoking Chrome, so checked-in artifact generation is deterministic.

## Pass 2 — CLI flow and dead-code audit
- Reviewed the compare-command control flow for unnecessary state and argument guardrails.
- Issue found: the first draft kept an unused temporary HTML variable after rendering, which made the PNG/export branch harder to scan during maintenance.
- Fix applied: simplified the compare branch so it writes the HTML artifact inline, then runs the PNG capture only when requested. The `--png-output` / `--html-output` guardrail stayed in place and is now covered by a focused test.

## Pass 3 — docs + committed artifact audit
- Re-ran the compare workflow and checked the README usage block, sample artifact bundle, and HTML sibling links.
- Issue found: the first README revision accidentally switched the test command to a repo-root path even though the snippet already `cd`s into the project directory.
- Fix applied: restored the project-local pytest command, regenerated the sample compare bundle with the PNG companion, and extended the HTML test coverage to assert the `PNG snapshot` link.

## Final verification
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- repo-root export smoke:
  - `mkdir -p /tmp/tarjan-png-slice && ./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --json-output /tmp/tarjan-png-slice/benchmark.json --csv-output /tmp/tarjan-png-slice/benchmark.csv --markdown-output /tmp/tarjan-png-slice/benchmark.md --html-output /tmp/tarjan-png-slice/benchmark.html --png-output /tmp/tarjan-png-slice/benchmark.png >/tmp/tarjan-png-slice/stdout.json`
- committed sample artifact smoke:
  - `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 5 --json-output docs/artifacts/tarjan-scc-lab/sample-compare.json --csv-output docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output docs/artifacts/tarjan-scc-lab/sample-compare.md --html-output docs/artifacts/tarjan-scc-lab/sample-compare.html --png-output docs/artifacts/tarjan-scc-lab/sample-compare.png >/tmp/tarjan-sample-png-stdout.json`
- `file docs/artifacts/tarjan-scc-lab/sample-compare.png`
- `git diff --check`
