# network-flow-lab

A portfolio-friendly algorithms lab that computes maximum flow with Edmonds-Karp, records each augmenting path, reports the resulting min cut, and now includes a bipartite-matching helper built on the same flow engine.

## Why it is interesting
- demonstrates a classic graph algorithm used in routing, scheduling, and resource allocation
- shows how residual graphs and breadth-first search interact in a clean implementation
- connects max flow to a second interview-friendly problem: maximum bipartite matching
- produces explainable output instead of only a final number
- gives interview-ready material around correctness, complexity, and cut/flow duality

## Features
- JSON graph input with named nodes and directed capacities
- Edmonds-Karp max-flow solver with deterministic BFS traversal
- step-by-step augmenting path log with bottleneck values
- per-edge flow summary and min-cut partition output
- bipartite-matching mode that reduces assignments to unit-capacity flow
- bundled sample flow graph and sample matching graph
- unit tests for correctness, validation, and CLI behavior

## Usage

Run the bundled sample flow graph:

```bash
python3 projects/network-flow-lab/network_flow.py demo --pretty
```

Solve a custom flow graph:

```bash
python3 projects/network-flow-lab/network_flow.py solve projects/network-flow-lab/sample_graph.json --pretty
```

Run the bundled bipartite-matching demo:

```bash
python3 projects/network-flow-lab/network_flow.py match-demo --pretty
```

Solve a custom bipartite-matching graph:

```bash
python3 projects/network-flow-lab/network_flow.py match projects/network-flow-lab/sample_matching_graph.json --pretty
```

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

## Test

```bash
python3 -m unittest tests/test_network_flow_lab.py
```

## Design notes
- Each BFS finds the shortest augmenting path in edge count, which yields Edmonds-Karp's `O(V * E^2)` worst-case bound.
- Reverse residual edges make it possible to reroute earlier decisions when a better later path is found.
- The reported min cut comes from the nodes still reachable from the source in the final residual graph.
- Maximum bipartite matching reduces cleanly to max flow by adding a super-source, a super-sink, and unit capacities on partition and compatibility edges.

## Future improvements
- export Graphviz diagrams for the flow network, residual graph, and final cut
- benchmark larger random graphs and compare with Dinic's algorithm
- add weighted assignment or min-cost flow as a follow-up advanced slice
