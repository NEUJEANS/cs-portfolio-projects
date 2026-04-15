# network-flow-lab

A portfolio-friendly algorithms lab that computes maximum flow with Edmonds-Karp, records each augmenting path, and reports the resulting min cut.

## Why it is interesting
- demonstrates a classic graph algorithm used in routing, scheduling, and resource allocation
- shows how residual graphs and breadth-first search interact in a clean implementation
- produces explainable output instead of only a final number
- gives interview-ready material around correctness, complexity, and cut/flow duality

## Features
- JSON graph input with named nodes and directed capacities
- Edmonds-Karp max-flow solver with deterministic BFS traversal
- step-by-step augmenting path log with bottleneck values
- per-edge flow summary and min-cut partition output
- sample graph for quick demos and unit tests for edge cases

## Usage

Run the bundled sample graph:

```bash
python3 projects/network-flow-lab/network_flow.py demo --pretty
```

Solve a custom graph:

```bash
python3 projects/network-flow-lab/network_flow.py solve projects/network-flow-lab/sample_graph.json --pretty
```

Graph format:

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

## Test

```bash
python3 -m unittest tests/test_network_flow_lab.py
```

## Design notes
- Each BFS finds the shortest augmenting path in edge count, which yields Edmonds-Karp's `O(V * E^2)` worst-case bound.
- Reverse residual edges make it possible to reroute earlier decisions when a better later path is found.
- The reported min cut comes from the nodes still reachable from the source in the final residual graph.

## Future improvements
- add bipartite-matching helpers that reduce matching problems to max flow
- export Graphviz diagrams for the flow and final cut
- benchmark larger random graphs and compare with Dinic's algorithm
