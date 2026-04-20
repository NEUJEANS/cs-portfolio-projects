# Dependency graph planner review — 2026-04-20 — benchmark export slice

## Pass 1 — docs / product-story review
- Re-read the planner README and checklist from the perspective of someone who only saw the Markdown benchmark report.
- Issue found: the project still underexplained that the benchmark suite could now feed downstream analysis with committed JSON/CSV artifacts, so the new export layer looked half-finished.
- Fix: updated `projects/dependency-graph-planner/README.md`, `projects/dependency-graph-planner/CHECKLIST.md`, the dated slice checklist, and the long-form project checklist to describe the export set clearly.

## Pass 2 — CLI validation / regression review
- Re-read the command-flag validation logic instead of trusting that new benchmark-specific flags were fully covered.
- Issue found: the suite exercised happy-path benchmark export writing, but there was no CLI-level regression proving `--benchmark-json-out` is rejected on non-benchmark commands.
- Fix: added `test_cli_plan_rejects_benchmark_export_flags` so command-specific validation is enforced through the real CLI path.

## Pass 3 — artifact / reproducibility review
- Replayed the benchmark export workflow like a user generating committed artifacts for GitHub browsing.
- Issue found: the dirty local slice had generated JSON/CSV files, but they were not yet captured as committed benchmark artifacts or called out in the project narrative.
- Fix: regenerated and checked the benchmark JSON + aggregate CSV + per-strategy CSV artifacts, confirmed repo-relative graph labels in the written outputs, and kept the artifact references aligned with the README/checklists.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark projects/dependency-graph-planner/portfolio_benchmark_suite.json --benchmark-markdown-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md --benchmark-json-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.json --benchmark-aggregate-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_aggregates.csv --benchmark-strategy-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_strategies.csv`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark projects/dependency-graph-planner/portfolio_benchmark_suite.json --json`
- deterministic double-export hash check for Markdown stdout/report plus both CSV exports, with normalized JSON payload comparison across two repeated export runs
- `git diff --check`
