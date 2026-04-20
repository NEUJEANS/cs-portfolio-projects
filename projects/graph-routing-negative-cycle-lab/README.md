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
- export Markdown routing reports that explain reachable vs unreachable nodes and Bellman-Ford iteration activity
- export Mermaid and Graphviz DOT artifacts that highlight Bellman-Ford shortest-path trees and reachable negative cycles
- compare two graph variants from the same source and emit route-table diffs covering edge-weight changes, predecessor swaps, path shifts, and cost deltas
- export route-table diff Markdown artifacts for release-review or routing-change walkthroughs
- export a static HTML diff dashboard with summary cards and audit tables for portfolio screenshots or walkthroughs
- export a compact SVG summary card for README thumbnails, slide decks, or quick review comments
- bundle several comparison scenarios into one static gallery landing page with linked Markdown, HTML, and SVG artifacts

## Usage
```bash
cd projects/graph-routing-negative-cycle-lab
python3 graph_routing_lab.py sample_graph.json --source A
python3 graph_routing_lab.py sample_graph.json --source A --format json
python3 graph_routing_lab.py sample_graph.json --mode johnson --format json
python3 graph_routing_lab.py negative_cycle_graph.json --source A --mode bellman-ford
python3 graph_routing_lab.py unreachable_graph.json --source A --export-markdown ../../docs/artifacts/graph-routing-negative-cycle-unreachable-report.md
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford --export-mermaid ../../docs/artifacts/graph-routing-negative-cycle-sample.mmd
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford --export-dot ../../docs/artifacts/graph-routing-negative-cycle-sample.dot
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford \
  --compare-graph route_shift_graph.json
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford \
  --compare-graph route_shift_graph.json \
  --export-compare-markdown ../../docs/artifacts/graph-routing-negative-cycle-route-diff-report.md
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford \
  --compare-graph route_shift_graph.json \
  --export-compare-html ../../docs/artifacts/graph-routing-negative-cycle-route-diff-dashboard.html
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford \
  --compare-graph route_shift_graph.json \
  --export-compare-svg ../../docs/artifacts/graph-routing-negative-cycle-route-diff-card.svg
python3 graph_routing_lab.py sample_graph.json --source A --mode bellman-ford \
  --compare-graph negative_cycle_graph.json \
  --export-compare-markdown ../../docs/artifacts/graph-routing-negative-cycle-incident-report.md \
  --export-compare-html ../../docs/artifacts/graph-routing-negative-cycle-incident-dashboard.html \
  --export-compare-svg ../../docs/artifacts/graph-routing-negative-cycle-incident-card.svg
python3 graph_routing_lab.py --gallery-manifest portfolio_gallery_manifest.json \
  --export-gallery-markdown ../../docs/artifacts/graph-routing-negative-cycle-gallery.md \
  --export-gallery-html ../../docs/artifacts/graph-routing-negative-cycle-gallery.html
python3 -m unittest ../../tests/test_graph_routing_negative_cycle_lab.py -v
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

## Sample comparison fixtures
- `route_shift_graph.json` changes two edge weights so the source `A` route table shifts from `A -> C -> B` to direct `A -> B`, while `D` keeps the same cost but moves to the alternate `A -> C -> D` path.
- `negative_cycle_graph.json` shows the harder failure mode where a candidate graph introduces a reachable negative cycle.
- `link_failure_graph.json` shows a partial outage where `D` becomes unreachable and the remaining stable routes get more expensive.
- `docs/artifacts/graph-routing-negative-cycle-route-diff-report.md`, `graph-routing-negative-cycle-route-diff-dashboard.html`, and `graph-routing-negative-cycle-route-diff-card.svg` are the committed artifact trio for the same-cost reroute story.
- `docs/artifacts/graph-routing-negative-cycle-incident-report.md`, `graph-routing-negative-cycle-incident-dashboard.html`, and `graph-routing-negative-cycle-incident-card.svg` are the committed artifact trio for the negative-cycle incident story.
- `docs/artifacts/graph-routing-negative-cycle-link-failure-report.md`, `graph-routing-negative-cycle-link-failure-dashboard.html`, and `graph-routing-negative-cycle-link-failure-card.svg` are the committed artifact trio for the link-failure regression story.
- `portfolio_gallery_manifest.json` plus `docs/artifacts/graph-routing-negative-cycle-gallery.{md,html}` bundle the three scenarios into one recruiter-friendly landing page.

## Testing focus
- Bellman-Ford shortest paths and predecessor chains
- reachable negative-cycle detection and reporting
- Johnson all-pairs correctness with negative edges but no negative cycles
- route-table diff coverage for edge-weight changes, cost deltas, and same-cost path swaps
- CLI JSON/pretty output smoke tests
- Markdown, HTML, and SVG comparison artifact coverage for routing-change walkthroughs
- gallery manifest + Markdown/HTML landing-page export coverage for multi-scenario portfolio bundles
- Markdown export coverage for unreachable nodes, iteration logs, negative-cycle explanations, and route-table comparison artifacts
- Mermaid and Graphviz DOT export artifact coverage
- input validation for duplicate nodes and invalid edge endpoints

## Future improvements
- compare Bellman-Ford vs DAG shortest-path performance on acyclic graphs
- optionally render DOT exports to PNG/SVG when `dot` is installed locally
- add incident-type filters or preset manifests so the gallery can pivot between reroute, outage, and negative-cycle stories
