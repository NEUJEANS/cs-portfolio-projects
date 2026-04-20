# Dependency graph planner wrap-up — 2026-04-20T01:41:02Z

- Project: `dependency-graph-planner`
- Commit hash: `fc85408` (`feat(dependency-graph-planner): compare scheduling strategies`)

## What changed
- added selectable worker-limited scheduling strategies (`critical-first`, `fifo`, `longest-processing-time`) to the CLI plus repeatable `--compare-strategy` support in the recruiter-friendly `report` workflow
- fixed strategy-report baseline ordering so the primary worker-limited schedule stays first and comparison deltas stay meaningful
- committed a dedicated `strategy_graph.json` showcase manifest plus Mermaid/DOT/report/schedule artifacts that demonstrate `critical-first` beating the other built-in heuristics at a fixed two-worker cap
- refreshed the dependency-graph README, checklist, research/learning notes, review log, and regenerated sample worker-limited artifacts so the new strategy metadata is visible in-repo

## Tests and reviews run
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`27/27`)
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --strategy fifo --json`
- `docs/reviews/2026-04-20-dependency-graph-strategy-comparison.md` (3 passes)
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add resource-class or environment-tag constraints so the planner can model tasks that require specialized runners instead of only a generic worker count.
