# Branch predictor budget-sweep CSV review — pass 1

- Scope: spreadsheet/export audit of the new CSV writer path
- Issue found: the first CSV export reused the human-facing Unicode separators from the Markdown helpers (`→` in the winner sequence and `·` in config labels), which is fine for docs but less friendly for spreadsheet imports, shell tooling, and plain-text diffing.
- Fix: added CSV-specific formatting helpers so `winner_sequence` uses ASCII `->` separators and `winner_config` uses `|` separators while keeping the Markdown/SVG rendering unchanged.
- Validation:
  - `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
  - `.venv/bin/pytest tests/test_branch_predictor_lab.py`
  - `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json`
- Result: the committed CSV stays spreadsheet-friendly without changing the nicer typography in the human-facing artifacts.
