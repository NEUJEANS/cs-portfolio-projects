# Branch predictor budget-sweep CSV review — pass 3

- Scope: docs and reproducibility audit
- Issue found: the new export path would have been easy to miss because the README quick-start / reproduce commands and the artifact gallery initially only surfaced Markdown/SVG outputs.
- Fix: updated the README budget-sweep examples, design notes, and future-improvements section; updated the artifact gallery to link the committed `budget-sweep.csv`; regenerated the committed CSV artifact alongside the Markdown/SVG pair.
- Validation:
  - checked `projects/branch-predictor-lab/README.md` budget-sweep commands now include `--csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv`
  - checked `docs/artifacts/branch-predictor-lab/index.md` links the CSV export in the budget-sweep section
  - checked `docs/artifacts/branch-predictor-lab/budget-sweep.csv` exists and matches the regenerated CLI output
- Result: the slice is now reproducible from docs alone, and the CSV artifact is discoverable instead of being hidden behind CLI help.
