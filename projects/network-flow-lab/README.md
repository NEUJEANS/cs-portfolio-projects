# network-flow-lab

A portfolio-friendly algorithms lab that computes maximum flow with Edmonds-Karp or Dinic, records each augmenting path, reports the resulting min cut, includes a bipartite-matching helper built on the same flow engine, and now ships a reproducible benchmark mode with multiple graph families, a bipartite minimum-vertex-cover explainer via König's theorem, Graphviz DOT export for explainable visuals, plus an optional proof view that narrates why the reported cut/cover certifies correctness.

## Why it is interesting
- demonstrates a classic graph algorithm used in routing, scheduling, and resource allocation
- shows how residual graphs and breadth-first search interact in a clean implementation
- connects max flow to a second interview-friendly problem: maximum bipartite matching
- demonstrates the matching/vertex-cover duality that often comes up in algorithms classes and interviews
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
- reproducible benchmark mode that compares Edmonds-Karp vs Dinic on random DAGs, dense residual-style meshes, or layered cut-stress graphs
- Graphviz DOT export for solved flow graphs and bipartite matchings
- optional `--explain` proof view that turns max-flow/min-cut and matching/cover results into compact correctness certificates
- standalone `--markdown-out` proof artifacts for flow and matching runs so portfolio screenshots do not require terminal capture
- bundled sample flow graph and sample matching graph
- unit tests for correctness, validation, CLI behavior, algorithm parity, and benchmark behavior

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

Export a DOT file for later rendering with Graphviz (the JSON response also includes a `dot_output` path when you use `--dot-out`):

```bash
python3 projects/network-flow-lab/network_flow.py demo --dot-out /tmp/network-flow.dot
python3 projects/network-flow-lab/network_flow.py demo --markdown-out /tmp/network-flow-proof.md
# optional render step if graphviz is installed:
# dot -Tpng /tmp/network-flow.dot -o /tmp/network-flow.png
```

Run the bundled bipartite-matching demo:

```bash
python3 projects/network-flow-lab/network_flow.py match-demo --pretty
python3 projects/network-flow-lab/network_flow.py match-demo --explain --pretty
```

Solve a custom bipartite-matching graph and export a DOT diagram. The JSON output includes `minimum_vertex_cover`, and the DOT output double-outlines cover vertices:

```bash
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --dot-out /tmp/matching.dot --pretty
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --markdown-out /tmp/matching-proof.md --pretty
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --algorithm dinic --pretty
```

Run reproducible benchmarks that compare Edmonds-Karp against Dinic across different generated graph families. In this pure-Python lab, Dinic is included for trade-off analysis rather than a guaranteed speed win on every small benchmark:

```bash
python3 projects/network-flow-lab/network_flow.py benchmark --nodes 24 --edge-probability 0.18 --trials 5 --seed 42 --pretty
python3 projects/network-flow-lab/network_flow.py benchmark --graph-family dense --nodes 18 --edge-probability 0.30 --trials 3 --seed 7 --pretty
python3 projects/network-flow-lab/network_flow.py benchmark --graph-family layered --nodes 18 --edge-probability 0.20 --trials 3 --seed 7 --pretty
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
- `docs/artifacts/network-flow-lab/sample-flow-proof.md`
- `docs/artifacts/network-flow-lab/sample-matching-proof.md`

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
- The benchmark mode generates reproducible graph families for three different stories: random DAGs, dense cyclic residual meshes, and layered cut-stress networks; it verifies both algorithms return the same max-flow value and summarizes elapsed time plus augmentation/phase counts.
- DOT export colors the source-side cut, sink-side cut, saturated cut edges, and chosen matching edges so the textual output and the diagram tell the same story.

## Future improvements
- add weighted assignment or min-cost flow as a follow-up advanced slice
- ship more polished SVG proof cards built on top of the Markdown artifact pipeline
- ship pre-rendered SVG examples in the docs for portfolio screenshots
- export benchmark runs as committed Markdown/SVG report cards for quick portfolio browsing
