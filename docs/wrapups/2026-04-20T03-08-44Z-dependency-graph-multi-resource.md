# Dependency graph planner wrap-up — 2026-04-20T03-08-44Z

- Project: `dependency-graph-planner`
- Feature commit: `47be980` (`feat(dependency-graph-planner): add multi-resource scheduling`)

## What changed
- extended manifests and scheduler output to support per-task multi-resource demand vectors while keeping legacy `resource_class` support for simple cases
- added a dedicated `multi_resource_graph.json` showcase manifest plus committed Mermaid, DOT, report, and schedule artifacts for the new bottleneck story
- refreshed the README, checklist, research/learning notes, review log, and older committed reports/schedule JSON artifacts so the portfolio docs match the current CLI output

## Tests and reviews run
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`34/34`)
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/multi_resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/multi_resource_graph.json --worker-limit 3 --resource-capacity browser-lab=3 --json`
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- `docs/reviews/2026-04-20-dependency-graph-multi-resource.md` (3 passes)

## Next step
- add a batch benchmark mode so multiple manifests can be replayed and heuristic schedules can be compared across a scenario suite instead of one example at a time.
