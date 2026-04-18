# Branch predictor budget sweep review — pass 2

- Scope: visual artifact audit of the committed SVG/Markdown outputs
- Issue found: the SVG legend hard-coded a subset of predictors, so when `always-taken` won the `random-biased` 64-bit bucket the color tile had no matching legend label.
- Fix: changed the legend to derive its entries from the actual sweep winners, ordered by the canonical predictor list.
- Validation:
  - `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --json`
  - legend check: confirmed `always-taken`, `two-bit`, `local-history`, `gshare`, `perceptron`, and `tournament` all appear before the grid markup in `docs/artifacts/branch-predictor-lab/budget-sweep.svg`
- Result: the committed winner matrix legend now matches the actual predictors shown in the artifact.
