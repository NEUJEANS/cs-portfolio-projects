# Branch predictor budget margin-trend wrap-up

- Timestamp: `2026-04-18T04:59:40Z`
- Commit: `3095912`

## What changed
- Added `summarize_budget_margin_story(...)` to turn budget-sweep results into near-tie counts, per-budget average winner gaps, and runner-up stability summaries.
- Extended the budget-sweep Markdown and SVG artifacts with a dedicated `Margin and runner-up story` section plus a new winner-margin trend card in the SVG.
- Updated CLI JSON output, tests, README/checklist notes, gallery copy, and added a review log for the slice.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `python3 -m unittest tests.test_branch_predictor_lab`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json > /tmp/branch_budget_sweep.json`
- Review log: `docs/reviews/2026-04-18-branch-predictor-margin-trend-review.md`
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Highlight budget crossover points where the winning predictor flips, so the artifact can call out the exact budgets that trigger architecture changes.
