# Branch predictor budget crossover wrap-up

- Timestamp: `2026-04-18T05:25:33Z`
- Commit: `e8667d3`

## What changed
- Added `summarize_budget_crossover_points(...)` so the budget sweep now records exact adjacent-budget winner flips, per-workload crossover sequences, and repeated transition counts across the whole grid.
- Extended the budget-sweep Markdown/SVG/CSV/JSON outputs with a dedicated crossover summary, workload-level trigger rows, and an SVG crossover callout card.
- Updated the branch-predictor README, artifact gallery copy, checklist state, and test coverage so the crossover slice is documented and resumable.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py`
- `python3 -m unittest tests.test_branch_predictor_lab`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json > /tmp/branch-predictor-budget-sweep.json`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json > /tmp/branch-predictor-budget-sweep-final.json`
- Review log: `docs/reviews/2026-04-18-branch-predictor-crossover-review.md`
- Secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Annotate crossover cells directly on the winner matrix or export a crossover-only slide card for even faster portfolio screenshots.
