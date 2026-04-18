# Branch predictor budget-grid summary wrap-up

- Timestamp: `2026-04-18T04-43-47Z`
- Commit: `76dc714`

## What changed
- Added `summarize_budget_winner_grid(...)` so the budget sweep can summarize winners across the entire workload × budget matrix.
- Extended the budget-sweep Markdown and SVG exports with a whole-grid winner summary, stacked-bar win totals, and a budget-by-predictor heatmap.
- Exposed the winner summary in budget-sweep JSON, updated tests, refreshed the committed artifact gallery/docs, and marked the checklist slice complete.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `python3 -m unittest tests.test_branch_predictor_lab`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json`
- Review pass 1: caught and fixed an accidental `winner_summary` injection into the plain `sweep` JSON payload.
- Review pass 2: caught and fixed README/checklist edit drift before commit.
- Review pass 3: diff + artifact sanity check for the new Markdown/SVG sections and committed gallery references.
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Add budget-grid runner-up stability or winner-margin trend artifacts so near-ties are visible alongside outright wins.
