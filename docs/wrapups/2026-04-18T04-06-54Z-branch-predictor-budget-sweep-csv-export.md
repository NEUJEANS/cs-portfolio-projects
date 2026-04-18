# branch-predictor-lab wrap-up

- Timestamp: 2026-04-18T04:06:54Z
- Project: `branch-predictor-lab`
- Implementation commit: `12efebb`

## What changed
- Added a new `--csv-out` path for the `budget-sweep` CLI plus renderer/writer helpers so the budget-normalized winner matrix can be reused in spreadsheets, charts, and slide decks without re-parsing Markdown.
- Kept the CSV export machine-friendly by normalizing CSV-only labels to ASCII separators, while leaving the Markdown/SVG artifacts readable for humans.
- Regenerated the committed budget-sweep artifacts, added focused tests, updated the README/gallery/checklists, and logged three review passes so the slice is reproducible.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep loop-heavy --budgets 1 --table-sizes 2 --history-bits-options 1 --weight-limits 15 --csv-out /tmp/branch_budget_tiny.csv --json`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review pass 1: replaced Unicode-only separators in CSV fields with ASCII-friendly export formatting
- review pass 2: confirmed tiny-budget CSV rows stay valid when no advanced predictor fits
- review pass 3: updated README/gallery discovery so the committed CSV artifact is reproducible from docs alone

## Next step
- Add table-size sweep artifacts that compare static PC collisions and dynamic gshare collisions side by side across the same workload family.
