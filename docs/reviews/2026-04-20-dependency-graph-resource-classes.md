# Dependency graph planner review — 2026-04-20 — renewable resource-class slice

## Pass 1 — end-to-end CLI wiring
- Re-read the partially implemented `resource_class` additions from the perspective of a user running the checked-in CLI, not just library helpers.
- Issue found: the planner could carry `resource_class` data in memory, but `run_command()` and the parser did not yet resolve manifest `resource_capacities` or expose CLI overrides, so the feature was incomplete from the actual portfolio entry point.
- Fix: wired manifest `resource_capacities` parsing/validation into `run_command()`, added repeatable `--resource-capacity class=count`, and made schedule/report commands resolve those capacities lazily through the shared schedule cache.

## Pass 2 — report readability for recruiters
- Re-read the generated Markdown as a recruiter-friendly artifact instead of a raw scheduling dump.
- Issue found: resource-constrained runs only exposed their bottleneck clearly in JSON/text schedule output; the Markdown report did not surface active resource caps, slot assignments, or resource utilization, so the new slice's story was easy to miss.
- Fix: extended `render_report_markdown()` with renewable-resource summary bullets, a resource-utilization table, resource columns in the worker-limited task table and timing table, and resource labels inside the deterministic execution walkthrough.

## Pass 3 — regression and artifact consistency
- Re-read the repo after the code changes looking for stale examples or tests that would drift from the new report shape.
- Issue found: the new resource columns changed report output for existing committed examples, and the repo still lacked a dedicated showcase manifest/artifact bundle proving why specialized runner constraints matter.
- Fix: expanded the regression suite for resource-constrained schedules, overrides, report content, and CLI misuse handling; updated the older report assertions; regenerated the affected committed artifacts; and added `resource_graph.json` plus linked Mermaid/DOT/report/schedule examples and README references.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --resource-capacity gpu=2 --json`
- `git diff --check`
