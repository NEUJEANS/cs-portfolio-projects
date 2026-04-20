# Dependency graph planner wrap-up — 2026-04-20T02:35:13Z

- Project: `dependency-graph-planner`
- Feature commit: `d9f18cb` (`feat(dependency-graph-planner): add renewable resource caps`)

## What changed
- added manifest-backed renewable `resource_capacities` plus repeatable `--resource-capacity class=count` overrides for the `schedule` and `report` CLI flows
- extended worker-limited scheduling output with per-task resource labels, slot assignments, and resource-class utilization summaries so specialized runner bottlenecks are visible in both JSON and Markdown
- committed a dedicated `resource_graph.json` showcase manifest plus Mermaid, DOT, report, and schedule artifacts that demonstrate how a single GPU slot stretches the makespan from `6` to `8`
- refreshed the dependency-graph README, checklist, research/learning notes, review log, and previously committed worker-limited artifacts so the new resource metadata is visible across the portfolio entry

## Tests and reviews run
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`32/32`)
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --resource-capacity gpu=2 --json`
- `docs/reviews/2026-04-20-dependency-graph-resource-classes.md` (3 passes)
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- support multi-resource demand vectors or benchmark-style scenario suites so the scheduler can compare richer bottlenecks than a single optional resource class.
