# Dependency graph planner review — 2026-04-20 — multi-resource slice

## Pass 1 — product-story / README review
- Re-read the slice from the perspective of a recruiter landing on the project page first.
- Issue found: the code already supported per-task multi-resource demands, but the README still described that capability as future work and did not expose a dedicated showcase manifest.
- Fix: rewrote the README sections that describe features, manifest format, usage examples, committed artifacts, and future improvements; added `multi_resource_graph.json` plus a resumable `CHECKLIST.md` for the project.

## Pass 2 — artifact consistency review
- Re-read the checked-in docs artifacts against the updated report/schedule schema.
- Issue found: previously committed report and schedule artifacts still used the old single-resource wording (`Resource class`, `Resource slot`, `total_work`) and therefore no longer matched current CLI output.
- Fix: regenerated the committed artifact bundle for `sample_graph`, `resource_graph`, and `strategy_graph`, and added the new `multi_resource_graph` Mermaid/DOT/report/schedule outputs.

## Pass 3 — constrained-schedule behavior review
- Re-ran the new multi-resource flow like a user trying both the default capacities and a CLI override.
- Issue found: without a dedicated smoke check in the verification notes, it was too easy to miss that increasing browser capacity alone only partially helps because the GPU remains the binding bottleneck.
- Fix: kept the override regression coverage in tests, added the multi-resource refresh note, and manually verified `--resource-capacity browser-lab=3` reduces makespan from `10` to `9` while leaving the GPU as the limiting factor.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/resource_graph_resource_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/multi_resource_graph.json --worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/multi_resource_graph_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/multi_resource_graph.json --worker-limit 3 --resource-capacity browser-lab=3 --json`
- `git diff --check`
