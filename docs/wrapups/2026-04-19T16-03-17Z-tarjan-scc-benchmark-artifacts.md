# Tarjan SCC Lab benchmark artifact export slice — 2026-04-19T16:03:17Z

## What changed
- safely fetched `origin`, confirmed local `main` had no remote drift, and picked the clearest unfinished Tarjan SCC follow-up from the checklist
- added `compare --csv-output` so Tarjan vs. Kosaraju timing runs can be exported as spreadsheet-friendly per-trial rows
- added `compare --markdown-output` so the lab can generate a portfolio-ready benchmark report with graph metadata, average timings, per-run timing tables, component roster bullets, and interview talking points
- refreshed the Tarjan SCC README/checklist docs and checked in a sample compare bundle under `docs/artifacts/tarjan-scc-lab/`
- recorded a dedicated 3-pass review log for the slice

## Tests and validation run
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py` (`22 passed`)
- committed artifact smoke:
  - `cd projects/tarjan-scc-lab && mkdir -p ../../docs/artifacts/tarjan-scc-lab && /home/user1_admin/.openclaw/workspace/cs-portfolio-projects/.venv/bin/python tarjan_scc_lab.py sample_graph.json compare --repeat 5 --csv-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.csv --markdown-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.md > ../../docs/artifacts/tarjan-scc-lab/sample-compare.json`
- repo-root export smoke:
  - `/home/user1_admin/.openclaw/workspace/cs-portfolio-projects/.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --csv-output /tmp/tarjan-compare.csv --markdown-output /tmp/tarjan-compare.md >/tmp/tarjan-compare.json`
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Reviews run
- pass 1: artifact workflow/docs audit; fixed the README export command so it creates the artifact directory before JSON shell redirection
- pass 2: CSV writer audit; replaced the manual CSV string builder with `csv.DictWriter` + `StringIO`
- pass 3: path/display and final smoke audit; regenerated the checked-in sample bundle from the project directory so the artifact keeps the cleaner `sample_graph.json` label shown in the docs
- detailed review log: `docs/reviews/2026-04-19-tarjan-scc-benchmark-artifacts-review.md`

## Feature commit
- `1addcc8191067ac6a4e0896fab689708788ddc2a`

## Next step
- add a small HTML benchmark card/gallery that reuses the compare JSON/CSV artifact bundle so the SCC comparison story can render directly inside a portfolio site
