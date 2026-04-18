# Branch predictor budget sweep review — pass 1

- Scope: robustness audit of the new `budget-sweep` flow
- Issue found: `run_budget_normalized_sweep()` assumed every budget had at least two fitting predictors and at least one advanced predictor. Tiny budgets (for example `1 bit`) could therefore crash on `runner_up` lookup or group-selection helpers.
- Fix: made simple/advanced group selection optional, preserved runner-up fallback safely, and rendered missing groups as `n/a` instead of raising.
- Validation:
  - `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
  - `.venv/bin/pytest tests/test_branch_predictor_lab.py`
  - `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep loop-heavy --budgets 1 --table-sizes 2 --history-bits-options 1 --weight-limits 15 --json`
- Result: tiny-budget sweep now returns `always-taken` / `always-not-taken` without crashing and reports `best_advanced_predictor: null`.
