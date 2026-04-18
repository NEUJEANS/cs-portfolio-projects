# Branch predictor budget-sweep CSV review — pass 2

- Scope: tiny-budget edge-case audit for the CSV path
- Issue found: none after the export helpers were normalized. The remaining risk was that a CSV row could become ambiguous when no advanced predictor fits the budget.
- Validation:
  - `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep loop-heavy --budgets 1 --table-sizes 2 --history-bits-options 1 --weight-limits 15 --csv-out /tmp/branch_budget_tiny.csv --json`
  - confirmed `/tmp/branch_budget_tiny.csv` keeps blank advanced-predictor columns instead of crashing or writing misleading placeholder text
  - confirmed `/tmp/branch_budget_tiny.json` still reports `best_advanced_predictor: null` and `csv_output`
- Result: the CSV export remains machine-friendly for the same tiny-budget cases already covered by the JSON/Markdown path.
