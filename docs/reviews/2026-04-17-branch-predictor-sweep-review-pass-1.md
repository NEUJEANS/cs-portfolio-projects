# 2026-04-17 branch predictor sweep review pass 1

## Focus
CLI/runtime integrity for the new `sweep` slice.

## Issue found
- The in-progress `sweep` implementation had broken string joins (`"\n"`) in three return paths, which left `projects/branch-predictor-lab/branch_predictor.py` uncompilable.

## Fix applied
- Repaired the summary-table, Markdown-render, and SVG-render join/return paths so the module compiles and the CLI can execute.

## Result
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py` now passes and the `sweep` command produces text/JSON output again.
