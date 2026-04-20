# Dependency graph planner review — 2026-04-20 — strategy comparison slice

## Pass 1 — primary-strategy baseline ordering
- Re-read the first draft of the strategy-comparison report against the intended `--strategy` / `--compare-strategy` contract.
- Issue found: the report table and summary could list comparison strategies before the primary worker-limited schedule, which flipped the baseline and produced misleading negative `Δ vs primary strategy` values.
- Fix: changed `render_report_markdown()` so the primary worker-limited schedule is always listed first, then re-ran the strategy-report smoke and kept a regression assertion on the expected `critical-first -> fifo -> longest-processing-time` ordering.

## Pass 2 — regression and CLI misuse coverage
- Re-read the new scheduling-strategy implementation from the perspective of a user trying the new flags in the wrong place.
- Issue found: the existing tests did not directly protect strategy-specific makespans, schedule JSON payloads, report artifact links, or the error paths for `--strategy` / `--compare-strategy` misuse.
- Fix: added regression coverage for strategy makespans/dispatch order, report summary/table content, per-strategy artifact export, and CLI failures when the strategy flags are used outside `schedule`/`report` or without `--worker-limit`.

## Pass 3 — portfolio discoverability
- Re-read the README and committed artifact set like a recruiter skimming for the strongest demo path.
- Issue found: the repo had no dedicated manifest showing why scheduler heuristics matter, so the new feature was easy to miss and the original sample graph did not visibly change makespan across strategies.
- Fix: added `projects/dependency-graph-planner/strategy_graph.json`, committed the linked Mermaid/DOT/report/schedule artifact bundle, and updated the README/checklist/research/learning notes so the strategy tradeoff story is visible in-repo.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_single_worker_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --compare-strategy fifo --compare-strategy longest-processing-time --report-markdown-out docs/artifacts/dependency-graph-planner/strategy_graph_strategy_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py schedule projects/dependency-graph-planner/strategy_graph.json --worker-limit 2 --strategy fifo --json`
- `git diff --check`
