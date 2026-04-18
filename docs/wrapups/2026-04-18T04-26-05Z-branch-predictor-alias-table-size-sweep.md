# branch-predictor-lab wrap-up

- Timestamp: 2026-04-18T04:26:05Z
- Project: `branch-predictor-lab`
- Implementation commit: `cb138df`

## What changed
- Added a new `table-size-sweep` CLI that batches the seeded synthetic workloads and reports static PC collisions, dynamic gshare live collisions, and paired two-bit vs gshare accuracy across multiple predictor table sizes.
- Added Markdown, SVG, and CSV renderers plus committed table-size sweep artifacts so the aliasing story is reusable in README screenshots, slide decks, and spreadsheet-friendly chart workflows.
- Updated tests, the project checklist, the README reproduction commands, and the artifact gallery so this slice is discoverable and reproducible without reading the source first.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py table-size-sweep --trace-dir artifacts/branch-predictor-lab/table-size-sweep --markdown-out docs/artifacts/branch-predictor-lab/table-size-sweep.md --svg-out docs/artifacts/branch-predictor-lab/table-size-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/table-size-sweep.csv --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py table-size-sweep alias-thrash perceptron-majority --table-sizes 4 16 64 --csv-out /tmp/branch-table-size-sweep-focused.csv --json`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review pass 1: fixed the stale checklist so the finished CSV export slice is marked complete and the next candidate slice now points at a real remaining gap
- review pass 2: refreshed the README quick-start and committed-artifact commands so both budget-sweep CSV output and the new table-size sweep are reproducible from docs alone
- review pass 3: added the new sweep to the artifact gallery and trace-setup notes so recruiters can discover the SVG/CSV bundle without hunting through git history

## Next step
- Add artifact-ready stacked bar / heatmap exports that summarize how often each predictor wins across the whole budget grid, not just per-workload rows.
