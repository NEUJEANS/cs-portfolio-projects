# Dependency graph planner review — 2026-04-19 — diagram export slice

## Pass 1 — DOT readability and diff-friendliness
- Re-read the new DOT renderer with the generated sample output open side-by-side.
- Issue found: the first draft emitted literal line breaks inside quoted DOT labels, which made node statements harder to diff and less conventional for Graphviz text artifacts.
- Fix: normalized DOT label escaping to emit `\n` sequences instead of literal newlines and kept a direct regression test for the critical-path node/edge styling.

## Pass 2 — Mermaid safety for real task names
- Re-read the Mermaid exporter from the perspective of a manifest containing spaces or quoted task names.
- Issue found: this slice depended on synthetic node IDs for safety, but the test suite did not explicitly prove that punctuation-heavy task names stay renderable and collision-resistant.
- Fix: added regression coverage for names with spaces and quotes so Mermaid output keeps stable synthetic IDs while escaping labels correctly.

## Pass 3 — portfolio discoverability
- Re-read the project README and committed artifact paths like a recruiter skimming the repo.
- Issue found: raw `.mmd` output alone was not the best discoverability story, and the README did not point to a Markdown-wrapped Mermaid example that GitHub can preview more naturally.
- Fix: committed `sample_graph_mermaid.md`, updated the README artifact list, and clarified the artifact directory description.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py diagram projects/dependency-graph-planner/sample_graph.json --format mermaid > /tmp/dependency-graph-sample.mmd`
- `python3 projects/dependency-graph-planner/dependency_graph_planner.py diagram projects/dependency-graph-planner/sample_graph.json --format dot > /tmp/dependency-graph-sample.dot`
- `git diff --check`
