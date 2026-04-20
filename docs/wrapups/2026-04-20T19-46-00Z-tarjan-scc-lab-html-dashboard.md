# Wrap-up — 2026-04-20T19:46:00Z — tarjan-scc-lab HTML dashboard

## What changed
- added direct `compare --json-output` support so Tarjan/Kosaraju benchmark bundles can be generated without shell redirection
- added a static `--html-output` dashboard that turns the compare payload into summary cards, per-trial timing bars, component cards, and sibling artifact links
- checked in the refreshed sample compare bundle under `docs/artifacts/tarjan-scc-lab/`, including the new HTML artifact for screenshot-friendly portfolio demos
- refreshed the Tarjan SCC README plus slice checklist, learning note, and 3-pass review log so the work is resumable and easier to extend later
- covered the new export flow with focused CLI/rendering tests, including relative-link portability for nested output folders

## Tests and reviews run
- review log: `docs/reviews/2026-04-20-tarjan-scc-html-dashboard-review.md`
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json compare --repeat 3 --json-output /tmp/tarjan-html-slice/benchmark.json --csv-output /tmp/tarjan-html-slice/benchmark.csv --markdown-output /tmp/tarjan-html-slice/benchmark.md --html-output /tmp/tarjan-html-slice/benchmark.html >/tmp/tarjan-html-slice/stdout.json`
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- feature commit: `6eb2290`

## Next step
- add a raster/PNG capture helper on top of the static HTML dashboard so the compare artifact can produce slide-ready images without a browser screenshot round-trip
