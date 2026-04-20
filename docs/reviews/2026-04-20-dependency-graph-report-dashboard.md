# Dependency graph planner review — 2026-04-20 — report dashboard + SVG slice

## Pass 1 — README / artifact-story review
- Re-read the project page and committed artifact directory from the perspective of someone landing on the repo after the benchmark slice.
- Issue found: the code/artifact bundle now included dashboard and SVG outputs, but the README and project checklist still described HTML/SVG browsing as future work and did not show the new `--report-html-out` workflow.
- Fix: updated the feature list, usage examples, committed artifact inventory, and checklist entries so the new dashboard/SVG story is visible without reading the Python file first.

## Pass 2 — artifact hygiene / reproducibility review
- Replayed the report commands like a user regenerating the committed portfolio bundle.
- Issue found: an earlier smoke pass left stray root-level scratch outputs (`ART_DIR/`, `REPORT_HTML`) that would clutter `git status` and make the slice less resumable.
- Fix: moved the scratch outputs to workspace trash, then reran the real report commands against the committed artifact paths only.

## Pass 3 — deterministic bundle review
- Rechecked the new dashboard/SVG exports with a reproducibility mindset instead of trusting the first successful render.
- Issue found: without an explicit double-export hash check, it would be easy to miss accidental nondeterminism from HTML/SVG rendering changes.
- Fix: reran the worker-comparison export twice and verified stable hashes for the committed dashboard + SVG pair, alongside the expanded regression coverage for relative links and artifact writing.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --report-html-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md --report-html-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --report-html-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/multi_resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md --report-html-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report_dashboard.html --diagram-output-dir docs/artifacts/dependency-graph-planner`
- deterministic double-export hash check for `docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report_dashboard.html` and `docs/artifacts/dependency-graph-planner/sample_graph_3_workers_schedule.svg`
- `git diff --check`
