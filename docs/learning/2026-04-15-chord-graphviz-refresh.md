# Chord Graphviz refresh

## Goal
Add a lightweight visualization slice without introducing non-standard Python dependencies.

## Quick refresh notes
- Graphviz DOT is plain text, so the lab can export diagrams without rendering binaries.
- `digraph` with labeled nodes/edges is enough for portfolio-ready topology and route diagrams.
- Clustering stabilization rounds with `subgraph cluster_*` makes convergence steps easy to inspect.
- Keeping DOT generation side-effect free makes it simple to test with substring assertions.

## Self-check
- Use `record` nodes to show node name plus identifier/metadata succinctly.
- Show ring successor edges separately from highlighted lookup hops.
- Keep route/stabilization export on top of existing JSON/report methods instead of duplicating logic.
