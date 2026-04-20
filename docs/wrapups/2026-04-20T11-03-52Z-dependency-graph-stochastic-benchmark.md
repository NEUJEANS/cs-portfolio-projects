# Dependency graph planner wrap-up — 2026-04-20T11:03:52Z

- Project: `dependency-graph-planner`
- Feature commit: `995eceb` (`feat(dependency-graph-planner): add stochastic benchmark replays`)

## What changed
- finished the in-progress stochastic-benchmark slice by adding optional `stochastic_durations` suite scenarios that replay task durations with seeded triangular sampling on top of the existing deterministic benchmark pipeline
- extended the benchmark JSON/Markdown/HTML/CSV outputs with robustness metrics such as average/p50/p90/worst sampled makespans, delta-vs-best, and best-finish rates
- opted the committed seeded stress scenarios in `projects/dependency-graph-planner/portfolio_benchmark_suite.json` into stochastic replays and regenerated the committed artifact bundle under `docs/artifacts/dependency-graph-planner/`
- refreshed the planner README/checklists and added slice-specific research, learning, and 3-pass review notes so the uncertainty story is visible and resumable in-repo
- added regression coverage for stochastic payload rendering plus invalid `low_factor <= mode_factor <= high_factor` validation

## Tests and reviews run
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`55/55`)
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py benchmark projects/dependency-graph-planner/portfolio_benchmark_suite.json --benchmark-markdown-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.md --benchmark-html-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report_dashboard.html --benchmark-json-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_report.json --benchmark-aggregate-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_aggregates.csv --benchmark-strategy-csv-out docs/artifacts/dependency-graph-planner/portfolio_benchmark_suite_strategies.csv`
- deterministic repeated benchmark stdout hash check for the suite JSON payload
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review log: `docs/reviews/2026-04-20-dependency-graph-stochastic-benchmark.md`

## Next step
- add compact per-scenario uncertainty cards (SVG/HTML) so the stochastic p50/p90/worst-case story is visible at a glance without opening the full benchmark tables
