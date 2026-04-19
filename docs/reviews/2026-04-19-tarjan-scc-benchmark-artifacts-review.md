# Tarjan SCC Lab review — 2026-04-19 — benchmark artifact exports

## Pass 1 — artifact workflow and README audit
- Re-read the new `compare --csv-output/--markdown-output` flow against the README quick-start commands.
- Issue found: the first draft's sample export command redirected JSON into `docs/artifacts/tarjan-scc-lab/` without creating that directory first, so the command could fail on a fresh clone before the Python CLI had a chance to create the CSV/Markdown parent directories.
- Fix applied: added an explicit `mkdir -p ../../docs/artifacts/tarjan-scc-lab` step to the README export workflow and then reran the committed sample-artifact command.

## Pass 2 — CSV/report writer audit
- Reviewed the new report helpers with an eye toward publishable artifacts and future field growth.
- Issue found: the first draft built CSV output by manually joining strings, which was unnecessarily fragile compared with the repo's usual `csv.DictWriter` pattern.
- Fix applied: switched `render_compare_csv()` to `csv.DictWriter` + `StringIO`, kept the row schema the same, and reran `py_compile` plus the focused pytest suite.

## Pass 3 — path/display and final smoke audit
- Re-ran the compare export flow from both the repo root and the project directory, then checked README/checklist consistency plus `git diff --check`.
- Issue found: running the CLI from the repo root intentionally renders the graph file as `projects/tarjan-scc-lab/sample_graph.json`, while the checked-in sample artifact and README excerpt are cleaner when generated from the project directory as `sample_graph.json`.
- Fix applied: regenerated the committed sample bundle from `projects/tarjan-scc-lab/` using the project-local command shown in the README so the checked-in Markdown artifact stays screenshot-friendly and aligned with the docs.

## Final verification
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- committed artifact smoke:
  - `cd projects/tarjan-scc-lab && mkdir -p ../../docs/artifacts/tarjan-scc-lab && /home/user1_admin/.openclaw/workspace/cs-portfolio-projects/.venv/bin/python tarjan_scc_lab.py sample_graph.json compare --repeat 5 --csv-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.md > ../../docs/artifacts/tarjan-scc-lab/sample-compare.json`
- repo-root export smoke:
  - `/home/user1_admin/.openclaw/workspace/cs-portfolio-projects/.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --csv-output /tmp/tarjan-compare.csv --markdown-output /tmp/tarjan-compare.md >/tmp/tarjan-compare.json`
- `git diff --check`
