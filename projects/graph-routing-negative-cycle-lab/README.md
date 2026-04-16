# graph-routing-negative-cycle-lab

A Python graph-routing lab that demonstrates Bellman-Ford single-source shortest paths, Johnson's all-pairs shortest paths, and explicit negative-cycle detection in one small, portfolio-friendly project.

## Why it is portfolio-worthy
- connects textbook shortest-path algorithms to a routing-style debugging workflow
- shows how negative edges and negative cycles change what "shortest path" even means
- includes step-by-step Bellman-Ford iteration snapshots for explainability
- uses Johnson's algorithm to handle all-pairs shortest paths on graphs with negative edges but no negative cycles
- keeps everything local, testable, and easy to demo from the command line

## Features
- load directed weighted graphs from JSON
- validate graph structure and edge endpoints
- run Bellman-Ford from a chosen source with iteration logs and predecessor tracing
- detect and reconstruct a reachable negative cycle
- run Johnson's algorithm and emit all-pairs shortest-path routes
- provide pretty or JSON CLI output for READMEs and automation
- export Mermaid and Graphviz DOT artifacts that highlight Bellman-Ford shortest-path trees and reachable negative cycles

## Usage
```bash
cd projects/graph-routing-negative-cycle-lab
python3 graph_routing_lab.py sample_graph.json --source A
python3 graph_routing_lab.py sample_graph.json --source A --format json
python3 graph_routing_lab.py sample_graph.json --mode johnson --format json
python3 graph_routing_lab.py negative_cycle_graph.json --source A --mode bellman-ford
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford --export-mermaid ../../docs/artifacts/graph-routing-negative-cycle-sample.mmd
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford --export-dot ../../docs/artifacts/graph-routing-negative-cycle-sample.dot
pytest -q ../../tests/test_graph_routing_negative_cycle_lab.py
```

## Graph JSON format
```json
{
  "name": "routing_demo",
  "nodes": ["A", "B", "C", "D"],
  "edges": [
    {"source": "A", "target": "B", "weight": 4},
    {"source": "A", "target": "C", "weight": 2},
    {"source": "C", "target": "B", "weight": -1},
    {"source": "B", "target": "D", "weight": 2}
  ]
}
```

## Testing focus
- Bellman-Ford shortest paths and predecessor chains
- reachable negative-cycle detection and reporting
- Johnson all-pairs correctness with negative edges but no negative cycles
- CLI JSON/pretty output smoke tests
- Mermaid and Graphviz DOT export artifact coverage
- input validation for duplicate nodes and invalid edge endpoints

## Future improvements
- compare Bellman-Ford vs DAG shortest-path performance on acyclic graphs
- add unreachable-node examples and path explanation markdown artifacts
- optionally render DOT exports to PNG/SVG when `dot` is installed locally
