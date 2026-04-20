# Tarjan SCC showcase landing-page slice — 2026-04-20 20:49 UTC

## What changed
- added a first-class `showcase-demo` CLI that writes recruiter-friendly Markdown/HTML landing pages for one Tarjan SCC graph and links the explain, condensation, and benchmark artifacts together
- made the showcase reuse `--compare-json-path` as the benchmark source of truth so the embedded timing snapshot stays aligned with the linked compare bundle
- added guardrails for invalid linked benchmark JSON, refreshed the README workflow, and committed a complete sample artifact bundle (`sample-explain`, `sample-condensation.{json,dot,mmd}`, `sample-showcase.{md,html}`) alongside the refreshed benchmark artifacts
- recorded the slice checklist, research, learning notes, and a 3-pass review log; also closed the previous PNG checklist by marking its already-pushed secret-scan/push steps complete

## Tests and reviews run
- `./.venv/bin/python -m py_compile projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
- `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py` (`35 passed`)
- real artifact-generation smokes for `compare`, `explain`, `condensation`, `dot`, `mermaid`, and `showcase-demo` against `projects/tarjan-scc-lab/sample_graph.json`
- `git diff --check`
- inline consistency audit confirming the committed showcase Markdown/HTML embed the exact average timings from `docs/artifacts/tarjan-scc-lab/sample-compare.json`
- TruffleHog secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0 verified`, `0 unknown`)
- review log: `docs/reviews/2026-04-20-tarjan-scc-showcase-review.md`

## Commit
- feature commit: `5632552` (`feat(tarjan-scc-lab): add showcase landing pages`)

## Next step
- add a small multi-graph showcase index so several Tarjan SCC fixtures can share one portfolio landing page with cross-graph topology and benchmark cards
