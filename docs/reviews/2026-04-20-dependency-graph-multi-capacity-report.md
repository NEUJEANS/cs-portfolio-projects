# Dependency graph planner review — 2026-04-20 — multi-capacity comparison slice

## Pass 1 — regression coverage for the new comparison path
- Re-read the unfinished `--compare-worker-limit` implementation against the existing test suite.
- Issue found: the first draft had no direct regression coverage proving comparison rows, summary wording, or deduped worker-limit inputs stayed stable.
- Fix: added report-render and JSON-artifact tests that assert the 1/2/3-worker comparison summary, table rows, and deduped comparison payload/artifact outputs.

## Pass 2 — CLI contract and misuse handling
- Re-read the parser/flag validation from the perspective of a user trying the new flag on the wrong command.
- Issue found: the compare flag behavior existed in code, but there was no explicit CLI regression test protecting the error path.
- Fix: added a CLI test that verifies `--compare-worker-limit` is rejected outside the `report` command with a clear error.

## Pass 3 — portfolio discoverability
- Re-read the README and committed artifact list like a recruiter or reviewer skimming for the best demo path.
- Issue found: the docs still stopped at the single-worker report, so the stronger 1-vs-2-vs-3 worker story was easy to miss.
- Fix: documented the repeatable comparison command, added the committed comparison artifact list, and regenerated a checked-in multi-capacity sample report with linked schedule JSON snapshots.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --worker-limit 1 --compare-worker-limit 2 --compare-worker-limit 3 --report-markdown-out docs/artifacts/dependency-graph-planner/sample_graph_worker_comparison_report.md --diagram-output-dir docs/artifacts/dependency-graph-planner`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py report projects/dependency-graph-planner/sample_graph.json --compare-worker-limit 2 --compare-worker-limit 3`
- `git diff --check`
