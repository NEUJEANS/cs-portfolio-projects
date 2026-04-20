# Tarjan SCC HTML dashboard review — 2026-04-20

## Pass 1 — trial-card wording audit
- Re-read the new HTML dashboard copy while checking how non-winning trials are labeled.
- Issue found: the first draft rendered the tie state as `Tie Wins`, which reads awkwardly in a portfolio artifact.
- Fix applied: added `_trial_winner_heading()` so the dashboard now says `Tie on timing` for ties while keeping `Tarjan wins` / `Kosaraju wins` for non-ties.

## Pass 2 — relative artifact-link portability audit
- Reviewed the sibling artifact links with an eye toward checked-in docs pages that may live in nested folders.
- Issue found: the first draft only had same-directory HTML link coverage, so a future refactor could silently break nested-output portability.
- Fix applied: updated the focused HTML rendering test to place the dashboard under `site/reports/` while the companion artifacts live under `artifacts/`, then asserted the generated `../../artifacts/...` links.

## Pass 3 — committed artifact bundle and docs audit
- Re-ran the compare workflow from `projects/tarjan-scc-lab/`, then checked the README command, linked artifact bundle, and `git diff --check` hygiene.
- Issue found: before this pass, the repo still only checked in JSON/CSV/Markdown compare artifacts, and `git diff --check` also exposed CRLF-style line endings in the generated CSV artifact as trailing-whitespace noise.
- Fix applied: pinned `render_compare_csv()` to `lineterminator='\n'`, regenerated the sample compare bundle with direct `--json-output`, `--csv-output`, `--markdown-output`, and `--html-output` paths from the project directory, and refreshed the README/checklist language to document the full static artifact workflow.

## Final verification
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- repo-root export smoke:
  - `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --json-output /tmp/tarjan-html-slice/benchmark.json --csv-output /tmp/tarjan-html-slice/benchmark.csv --markdown-output /tmp/tarjan-html-slice/benchmark.md --html-output /tmp/tarjan-html-slice/benchmark.html >/tmp/tarjan-html-slice/stdout.json`
- committed sample artifact smoke:
  - `cd projects/tarjan-scc-lab && /home/user1_admin/.openclaw/workspace/cs-portfolio-projects/.venv/bin/python tarjan_scc_lab.py sample_graph.json compare --repeat 5 --json-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.json --csv-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.md --html-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.html >/tmp/tarjan-sample-stdout.json`
- `git diff --check`
