# network-flow-lab

A portfolio-friendly algorithms lab that computes maximum flow with Edmonds-Karp or Dinic, records each augmenting path, reports the resulting min cut, includes a bipartite-matching helper built on the same flow engine, extends that story into weighted assignment via min-cost flow, and now also solves generic source/sink min-cost-flow graphs with reusable proof artifacts. The lab ships a reproducible benchmark mode with multiple graph families, a bipartite minimum-vertex-cover explainer via König's theorem, Graphviz DOT export for explainable visuals across flow/matching/generic cost-flow variants, plus optional proof views that narrate why the reported cut/cover/cost certificate is correct.

## Why it is interesting
- demonstrates a classic graph algorithm used in routing, scheduling, and resource allocation
- shows how residual graphs and breadth-first search interact in a clean implementation
- connects max flow to interview-friendly follow-ups: maximum bipartite matching, weighted assignment, and generic min-cost shipping/routing graphs
- demonstrates the matching/vertex-cover duality that often comes up in algorithms classes and interviews
- shows how min-cost flow turns a weighted bipartite graph into an optimization story instead of only a feasibility story, then generalizes the same engine to reusable source/sink costed networks
- produces explainable output instead of only a final number
- gives interview-ready material around correctness, complexity, and cut/flow duality
- adds visualization-ready artifacts that make demos and README screenshots easier to build

## Features
- JSON graph input with named nodes and directed capacities
- Edmonds-Karp max-flow solver with deterministic BFS traversal
- Dinic max-flow solver with level-graph phases for side-by-side algorithm comparisons
- step-by-step augmenting path log with bottleneck values
- per-edge flow summary and min-cut partition output
- bipartite-matching mode that reduces assignments to unit-capacity flow
- minimum vertex cover recovery for bipartite graphs using alternating paths after the matching is found
- weighted assignment mode that solves a min-cost max-flow reduction with successive shortest augmenting paths
- generic min-cost-flow mode for custom source/sink graphs with capacities, non-negative edge costs, and optional `target_flow`
- committed weighted-assignment Markdown/SVG proof artifacts for portfolio screenshots without terminal capture
- committed generic min-cost-flow Markdown/SVG proof artifacts for portfolio screenshots without terminal capture
- reproducible benchmark mode that compares Edmonds-Karp vs Dinic on random DAGs, dense residual-style meshes, or layered cut-stress graphs
- standalone benchmark report-card export in Markdown and SVG for quick portfolio screenshots and README embeds
- Graphviz DOT export for solved flow graphs, bipartite matchings, and generic min-cost-flow graphs
- optional `--explain` proof view that turns max-flow/min-cut and matching/cover results into compact correctness certificates
- standalone `--markdown-out` proof artifacts for flow, matching, assignment, and generic min-cost-flow runs so portfolio screenshots do not require terminal capture
- standalone `--svg-out` proof cards for flow, matching, assignment, and generic min-cost-flow runs so the project ships screenshot-ready visual summaries without Graphviz
- bundled sample flow, matching, weighted-assignment, and generic cost-flow graphs
- unit tests for correctness, validation, CLI behavior, algorithm parity, min-cost-flow behavior, and benchmark behavior

## Usage

Run the bundled sample flow graph:

```bash
python3 projects/network-flow-lab/network_flow.py demo --pretty
python3 projects/network-flow-lab/network_flow.py demo --algorithm dinic --pretty
python3 projects/network-flow-lab/network_flow.py demo --explain --pretty
```

Solve a custom flow graph:

```bash
python3 projects/network-flow-lab/network_flow.py solve projects/network-flow-lab/sample_graph.json --pretty
python3 projects/network-flow-lab/network_flow.py solve projects/network-flow-lab/sample_graph.json --algorithm dinic --pretty
```

Export DOT, Markdown, or a standalone SVG proof card for later sharing (the JSON response includes the output paths you request):

```bash
python3 projects/network-flow-lab/network_flow.py demo --dot-out /tmp/network-flow.dot
python3 projects/network-flow-lab/network_flow.py demo --markdown-out /tmp/network-flow-proof.md
python3 projects/network-flow-lab/network_flow.py demo --svg-out /tmp/network-flow-proof.svg
# optional render step if graphviz is installed:
# dot -Tpng /tmp/network-flow.dot -o /tmp/network-flow.png
```

Run the bundled bipartite-matching demo:

```bash
python3 projects/network-flow-lab/network_flow.py match-demo --pretty
python3 projects/network-flow-lab/network_flow.py match-demo --explain --pretty
```

Solve a custom bipartite-matching graph and export a DOT diagram, Markdown proof, or SVG proof card. The JSON output includes `minimum_vertex_cover`, and the DOT output double-outlines cover vertices:

```bash
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --dot-out /tmp/matching.dot --pretty
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --markdown-out /tmp/matching-proof.md --pretty
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --svg-out /tmp/matching-proof.svg --pretty
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --algorithm dinic --pretty
```

Run the bundled weighted-assignment sample or solve a custom weighted bipartite graph. This uses a successive-shortest-path min-cost-flow solver and returns the chosen assignment edges plus total cost:

```bash
python3 projects/network-flow-lab/network_flow.py assign-demo --pretty
python3 projects/network-flow-lab/network_flow.py assign-demo --explain --pretty
python3 projects/network-flow-lab/network_flow.py assign projects/network-flow-lab/sample_assignment_graph.json --markdown-out /tmp/assignment-proof.md --pretty
python3 projects/network-flow-lab/network_flow.py assign projects/network-flow-lab/sample_assignment_graph.json --svg-out /tmp/assignment-proof.svg --pretty
```

Run the bundled generic min-cost-flow sample or solve a custom costed network. This mode keeps the same min-cost engine but drops the bipartite-only assumptions, so it works for small shipping/routing-style source/sink graphs too:

```bash
python3 projects/network-flow-lab/network_flow.py cost-demo --pretty
python3 projects/network-flow-lab/network_flow.py cost-demo --explain --pretty
python3 projects/network-flow-lab/network_flow.py cost-demo --dot-out /tmp/cost-flow.dot
python3 projects/network-flow-lab/network_flow.py cost-solve projects/network-flow-lab/sample_cost_flow_graph.json --markdown-out /tmp/cost-flow-proof.md --pretty
python3 projects/network-flow-lab/network_flow.py cost-solve projects/network-flow-lab/sample_cost_flow_graph.json --svg-out /tmp/cost-flow-proof.svg --pretty
```

Weighted-assignment format:

```json
{
  "left": ["anna", "ben", "chloe"],
  "right": ["api", "compiler", "database"],
  "edges": [
    {"source": "anna", "target": "api", "cost": 8},
    {"source": "anna", "target": "compiler", "cost": 4},
    {"source": "ben", "target": "api", "cost": 2},
    {"source": "chloe", "target": "database", "cost": 6}
  ]
}
```

Generic min-cost-flow format (non-negative costs only, with optional `target_flow` if you want a fixed amount shipped before the solver stops):

```json
{
  "nodes": ["s", "a", "b", "t"],
  "source": "s",
  "sink": "t",
  "target_flow": 2,
  "edges": [
    {"source": "s", "target": "a", "capacity": 2, "cost": 0},
    {"source": "s", "target": "b", "capacity": 1, "cost": 0},
    {"source": "a", "target": "t", "capacity": 1, "cost": 4},
    {"source": "a", "target": "b", "capacity": 1, "cost": 1},
    {"source": "b", "target": "t", "capacity": 2, "cost": 2}
  ]
}
```

Run reproducible benchmarks that compare Edmonds-Karp against Dinic across different generated graph families. In this pure-Python lab, Dinic is included for trade-off analysis rather than a guaranteed speed win on every small benchmark:

```bash
python3 projects/network-flow-lab/network_flow.py benchmark --nodes 24 --edge-probability 0.18 --trials 5 --seed 42 --pretty
python3 projects/network-flow-lab/network_flow.py benchmark --graph-family dense --nodes 18 --edge-probability 0.30 --trials 3 --seed 7 --pretty
python3 projects/network-flow-lab/network_flow.py benchmark --graph-family layered --nodes 18 --edge-probability 0.20 --trials 3 --seed 7 --pretty
python3 projects/network-flow-lab/network_flow.py benchmark --graph-family layered --nodes 18 --edge-probability 0.20 --trials 3 --seed 7 --markdown-out /tmp/network-flow-benchmark.md --svg-out /tmp/network-flow-benchmark.svg
```

Benchmark graph families:
- `dag` keeps the original acyclic baseline for easy apples-to-apples comparisons.
- `dense` adds many source/sink shortcuts plus guaranteed backward middle-layer edges, which creates more residual rerouting opportunities (requires at least 4 nodes).
- `layered` builds dense adjacent layers with optional skip edges, which makes cut-heavy phases easier to demo (requires at least 6 nodes).

Flow graph format:

```json
{
  "nodes": ["s", "a", "b", "t"],
  "source": "s",
  "sink": "t",
  "edges": [
    {"source": "s", "target": "a", "capacity": 3},
    {"source": "s", "target": "b", "capacity": 2},
    {"source": "a", "target": "t", "capacity": 2},
    {"source": "b", "target": "t", "capacity": 3}
  ]
}
```

Bipartite matching format:

```json
{
  "left": ["anna", "ben", "chloe"],
  "right": ["api", "compiler", "database"],
  "edges": [
    {"source": "anna", "target": "api"},
    {"source": "anna", "target": "compiler"},
    {"source": "ben", "target": "database"},
    {"source": "chloe", "target": "compiler"}
  ]
}
```

Committed sample proof artifacts:
- `docs/artifacts/network-flow-lab/index.md`
- `docs/artifacts/network-flow-lab/sample-flow-proof.md`
- `docs/artifacts/network-flow-lab/sample-flow-proof.svg`
- `docs/artifacts/network-flow-lab/sample-matching-proof.md`
- `docs/artifacts/network-flow-lab/sample-matching-proof.svg`
- `docs/artifacts/network-flow-lab/sample-assignment-proof.md`
- `docs/artifacts/network-flow-lab/sample-assignment-proof.svg`
- `docs/artifacts/network-flow-lab/sample-cost-flow.dot`
- `docs/artifacts/network-flow-lab/sample-cost-flow-proof.md`
- `docs/artifacts/network-flow-lab/sample-cost-flow-proof.svg`
- `docs/artifacts/network-flow-lab/benchmark-dag-report.md`
- `docs/artifacts/network-flow-lab/benchmark-dag-report.svg`
- `docs/artifacts/network-flow-lab/benchmark-dense-report.md`
- `docs/artifacts/network-flow-lab/benchmark-dense-report.svg`
- `docs/artifacts/network-flow-lab/benchmark-layered-report.md`
- `docs/artifacts/network-flow-lab/benchmark-layered-report.svg`

## Test

```bash
python3 -m unittest tests/test_network_flow_lab.py
```

## Design notes
- Edmonds-Karp uses BFS to find the shortest augmenting path in edge count, which yields the classic `O(V * E^2)` worst-case bound.
- Dinic builds a BFS level graph, then pushes blocking flows with DFS-style traversal, which often reduces the amount of repeated path work in practice.
- Reverse residual edges make it possible to reroute earlier decisions when a better later path is found.
- The reported min cut comes from the nodes still reachable from the source in the final residual graph.
- `--explain` turns that residual reachability into a compact certificate by summing the cut edges and checking that their capacity equals the computed max flow.
- Maximum bipartite matching reduces cleanly to max flow by adding a super-source, a super-sink, and unit capacities on partition and compatibility edges.
- Once a maximum matching is known, the lab derives a minimum vertex cover by alternating-path reachability from unmatched left-side vertices, giving a constructive König's theorem witness.
- In matching mode, `--explain` surfaces the alternating-path reachability sets and the recovered cover vertices so the proof can be demoed without reading code.
- Weighted assignment is modeled as a min-cost max-flow reduction with unit capacities on left/right partitions and non-negative costs on compatibility edges; successive shortest augmenting paths with reduced-cost potentials keep the residual shortest-path search deterministic and interview-explainable.
- The same min-cost engine now also accepts generic source/sink costed-flow graphs with capacities, non-negative costs, and an optional `target_flow`, which makes the project useful for small shipping/routing stories beyond bipartite assignment.
- Generic min-cost-flow DOT export labels each edge with `flow/capacity @ cost`, so the chosen shipment paths can be diagrammed alongside the Markdown/SVG proof artifacts.
- The benchmark mode generates reproducible graph families for three different stories: random DAGs, dense cyclic residual meshes, and layered cut-stress networks; it verifies both algorithms return the same max-flow value and summarizes elapsed time plus augmentation/phase counts.
- Benchmark report-card export turns one benchmark run into committed Markdown/SVG artifacts with setup details, trial tables, and interview-ready headline metrics.
- The standalone proof-card SVG export gives you screenshot-ready correctness summaries for both raw max-flow runs and bipartite-match reductions without requiring Graphviz.
- DOT export colors the source-side cut, sink-side cut, saturated cut edges, and chosen matching edges so the textual output and the diagram tell the same story.

## Future improvements
- add Graphviz DOT export for weighted-assignment reductions so the bipartite min-cost story can be diagrammed directly too
- render actual node-link SVG layouts for solved flow, matching, assignment, and generic min-cost-flow proofs instead of card-style summaries
- add a tiny static web gallery that lets viewers toggle between Markdown, SVG, DOT, and raw JSON artifacts
