# 2026-04-17 branch predictor sweep review pass 2

## Focus
Regression coverage for the new batch-sweep workflow.

## Issue found
- The repo had no automated coverage for `run_workload_sweep()`, sweep rendering helpers, or the `sweep --trace-dir/--markdown-out/--svg-out --json` CLI path, so the new slice could have silently drifted.

## Fix applied
- Added targeted unit/CLI tests that verify profile-driven configs, written trace files, Markdown/SVG output generation, and the text summary helper.

## Result
- `python3 -m unittest tests.test_branch_predictor_lab` now covers the sweep slice end-to-end instead of only single-trace compare/simulate flows.
