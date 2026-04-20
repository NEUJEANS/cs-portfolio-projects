# Dependency graph planner review — 2026-04-20 — benchmark dashboard slice

## Pass 1 — docs / product-story review
- Re-read the planner README and checklist from the perspective of someone browsing the benchmark suite after the previous JSON/CSV export slice.
- Issue found: the repo still described the benchmark bundle mainly as Markdown/JSON/CSV outputs, so the new dashboard flow was invisible in the project story.
- Fix: updated `projects/dependency-graph-planner/README.md`, `projects/dependency-graph-planner/CHECKLIST.md`, the dated slice checklist, and the long-form project checklist to call out the benchmark dashboard workflow and committed HTML artifact explicitly.

## Pass 2 — CLI validation / renderer review
- Re-read the benchmark render/write path instead of assuming the new dashboard flag was fully covered because the report-dashboard slice already existed.
- Issue found: the unfinished local slice rendered the benchmark dashboard happy path, but there was no dedicated CLI-level regression proving `--benchmark-html-out` is rejected on non-benchmark commands.
- Fix: kept the benchmark renderer wired through the existing result payload and added `test_cli_plan_rejects_benchmark_html_flag` plus dashboard artifact-link tests.

## Pass 3 — artifact / reproducibility review
- Replayed the benchmark export workflow like a user generating committed portfolio artifacts.
- Issue found: the benchmark bundle still lacked a checked-in HTML dashboard artifact and the written report/json metadata had not yet been refreshed to link the full bundle together.
- Fix: regenerated `docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report_dashboard.html`, refreshed the Markdown/JSON artifacts with linked bundle metadata, and verified the repeated export stays deterministic.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark projects/dependency-graph-planner/portfolio_benchmark_suite.json --benchmark-markdown-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md --benchmark-html-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report_dashboard.html --benchmark-json-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.json --benchmark-aggregate-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_aggregates.csv --benchmark-strategy-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_strategies.csv`
- deterministic double-export hash check for Markdown/HTML/JSON/CSV bundle outputs with the same export flags
- `git diff --check`
