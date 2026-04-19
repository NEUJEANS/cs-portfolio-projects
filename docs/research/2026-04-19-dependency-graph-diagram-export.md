# 2026-04-19 dependency graph diagram export research

## Goal
Add a lightweight visualization slice to `dependency-graph-planner` so the project can emit recruiter-friendly dependency maps without adding rendering-time dependencies.

## Brief findings
- Mermaid `flowchart LR` is a good fit for dependency DAGs because GitHub-friendly Markdown can render it directly and the left-to-right layout matches pipeline intuition.
- Mermaid lets node text differ from node IDs, so the exporter can use stable synthetic IDs while still showing readable task labels with duration/slack metadata.
- Graphviz DOT is still worth exporting alongside Mermaid because it is deterministic plain text, easy to diff in git, and can be rendered later to SVG/PNG in offline workflows.
- DOT `subgraph { rank=same; ... }` is a simple way to keep same-layer tasks aligned without changing the underlying dependency edges.
- Highlighting the critical path in both output modes makes the diagram more than a raw graph dump; it reinforces the scheduling story already computed by the planner.

## Sources consulted
- Mermaid flowchart syntax docs: https://mermaid.js.org/syntax/flowchart.html
- Graphviz DOT language docs: https://graphviz.org/doc/info/lang.html
