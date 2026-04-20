# Tarjan SCC showcase landing page

A compact landing page that ties together the SCC explanation, condensation views, and Tarjan-vs.-Kosaraju benchmark bundle for one graph.

## Snapshot
| metric | value |
| --- | --- |
| graph file | `projects/tarjan-scc-lab/sample_graph.json` |
| node count | 8 |
| edge count | 10 |
| strongly connected components | 4 |
| condensation levels | 4 |
| cyclic components | 3 |
| benchmark repeat count | 5 |
| algorithms match | yes |
| average winner | Tarjan |

## Explanation preview
```text
Graph has 8 nodes, 10 directed edges, and 4 strongly connected components.
Largest component size: 3.
Condensation DAG spans 4 topological level(s).
C0 (level 0, role source, in=0, out=1): A, B, C
C1 (level 1, role bridge, in=1, out=1): D, E
C2 (level 2, role bridge, in=1, out=1): F, G
C3 (level 3, role sink, in=1, out=0): H
```

## Topology groups
- level 0 — 1 component(s): C0 (A, B, C)
- level 1 — 1 component(s): C1 (D, E)
- level 2 — 1 component(s): C2 (F, G)
- level 3 — 1 component(s): C3 (H)

## Interview storyline
- Tarjan and Kosaraju agree on the deterministic SCC grouping for this graph.
- The condensation DAG compresses the graph into 4 SCC node(s) spread across 4 topological level(s).
- Average timing winner: Tarjan (0.008428 ms Tarjan vs. 0.014586 ms Kosaraju).

## Linked artifact bundles

### Walkthrough snapshot
Start with the concise SCC explanation before jumping into the diagram and benchmark artifacts.
- [Explain text](sample-explain.txt) — Plain-text interview walkthrough of the graph and topological SCC story.

### Condensation views
Use whichever representation fits the audience: JSON for tooling, DOT for Graphviz, Mermaid for markdown-native docs.
- [Condensation JSON](sample-condensation.json) — Machine-readable SCC condensation DAG with topology groups.
- [Graphviz DOT](sample-condensation.dot) — Diagram source for Graphviz or slide-friendly rendered images.
- [Mermaid flowchart](sample-condensation.mmd) — GitHub-friendly markup for README and markdown embeds.

### Benchmark bundle
Compare Tarjan and Kosaraju through raw timings, a Markdown write-up, a browser-ready dashboard, and a PNG snapshot.
- [Benchmark JSON](sample-compare.json) — Machine-readable timing payload with component roster and averages.
- [Benchmark CSV](sample-compare.csv) — Trial-by-trial timing rows for spreadsheets or charts.
- [Benchmark Markdown](sample-compare.md) — Portfolio-ready benchmark report with tables and talking points.
- [Benchmark HTML](sample-compare.html) — Static dashboard for browser demos or GitHub Pages hosting.
- [Benchmark PNG](sample-compare.png) — Slide-ready screenshot captured from the dashboard.
