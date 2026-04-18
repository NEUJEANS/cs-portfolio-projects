# Branch predictor budget sweep review — pass 3

- Scope: CLI/docs reproducibility audit
- Issue found: the JSON payload for `budget-sweep` omitted the trace directory even when `--trace-dir` was used, which made wrap-ups and downstream tooling less reproducible than the existing `sweep` command.
- Fix: added top-level `trace_dir` to the JSON payload, added test coverage for it, and updated the README/gallery/checklist so the committed artifact can be regenerated from docs alone.
- Validation:
  - `.venv/bin/pytest tests/test_branch_predictor_lab.py`
  - confirmed `/tmp/branch_budget_sweep.json` contains `"trace_dir": "artifacts/branch-predictor-lab/budget-sweep"`
  - confirmed `artifacts/branch-predictor-lab/budget-sweep/loop-heavy-seed7.trace` exists after regeneration
- Result: the slice is now reproducible from the project docs, CLI JSON, and committed artifacts without extra tribal knowledge.
