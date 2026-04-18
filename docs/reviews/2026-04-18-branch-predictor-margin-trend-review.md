# Branch predictor budget margin-trend review

- Timestamp: `2026-04-18T04:58:50Z`
- Project: `branch-predictor-lab`
- Slice: budget-grid runner-up stability + winner-margin trend artifacts

## Review pass 1 — regression/unit coverage
- Ran `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- Ran `python3 -m unittest tests.test_branch_predictor_lab`
- Issue found: the first edit accidentally injected the new margin-summary block into `render_sweep_markdown(...)`, which broke the non-budget sweep path with `NameError: margin_summary is not defined`.
- Fix: restored `render_sweep_markdown(...)` to the original trace-family sweep structure and kept the new summary logic scoped to `render_budget_sweep_markdown(...)` / `render_budget_sweep_svg(...)` only.

## Review pass 2 — artifact/report content
- Re-read the generated `docs/artifacts/branch-predictor-lab/budget-sweep.md` output after the first fix.
- Issue found: the budget-sweep Markdown export still skipped the new `## Margin and runner-up story` section because the initial patch matched the wrong `## Per-workload notes` anchor.
- Fix: reinserted the margin/race summary block directly inside `render_budget_sweep_markdown(...)` before the per-workload notes section.

## Review pass 3 — final runnable smoke + docs consistency
- Ran `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- Ran `python3 projects/branch-predictor-lab/branch_predictor.py budget-sweep --trace-dir artifacts/branch-predictor-lab/budget-sweep --markdown-out docs/artifacts/branch-predictor-lab/budget-sweep.md --svg-out docs/artifacts/branch-predictor-lab/budget-sweep.svg --csv-out docs/artifacts/branch-predictor-lab/budget-sweep.csv --json > /tmp/branch_budget_sweep.json`
- Checked the emitted JSON summary and the generated Markdown artifact for the new margin/runner-up sections.
- Result: no further issues found. The runnable artifact flow now emits whole-grid win totals, a budget winner heatmap, and the new near-tie / runner-up stability story together.
