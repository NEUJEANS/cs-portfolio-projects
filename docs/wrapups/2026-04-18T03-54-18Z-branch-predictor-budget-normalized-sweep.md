# branch-predictor-lab wrap-up

- Timestamp: 2026-04-18T03:54:18Z
- Project: `branch-predictor-lab`
- Implementation commit: `7027a21`

## What changed
- Added a new `budget-sweep` CLI that searches the best-fitting predictor config under shared approximate state-bit budgets and reports winners across all built-in synthetic workloads.
- Added state-bit estimation helpers, Markdown/SVG budget artifacts, committed generated traces under `artifacts/branch-predictor-lab/budget-sweep/`, and gallery/README/checklist updates so the slice is reproducible.
- Added budget-focused unit/CLI tests plus three review logs covering tiny-budget robustness, SVG legend completeness, and JSON/docs reproducibility.

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep loop-heavy --budgets 1 --table-sizes 2 --history-bits-options 1 --weight-limits 15 --json`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review pass 1: fixed tiny-budget crashes when no advanced predictor fits
- review pass 2: fixed SVG legend drift so stateless/simple winners appear in the legend when they actually win
- review pass 3: added `trace_dir` to the JSON payload and aligned README/gallery docs with the committed artifact paths

## Next step
- Add CSV/export-friendly budget sweep output so README charts and slide decks can reuse the same winner matrix without re-parsing Markdown.
