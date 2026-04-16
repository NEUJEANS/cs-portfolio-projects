# splay-tree-lab checklist

## Status
- [x] vertical slice 6 complete

## Core functionality
- [x] define portfolio goals for a self-adjusting BST lab with resumable snapshots
- [x] refresh splay rotation patterns, access locality, and delete/join behavior
- [x] implement build/show/access/insert/delete snapshot workflows
- [x] add split/join support for disjoint value sets and pivot-based partitioning
- [x] persist split partitions as resumable snapshots with useful root metadata
- [x] add traced access summaries with per-step comparison and rotation counts
- [x] export before/after Graphviz DOT and Mermaid diagrams for access traces
- [x] compare hot-set and uniform-random workloads against `red-black-tree-lab`
- [x] export benchmark results as portfolio-ready JSON and CSV artifacts
- [x] cover direct behavior plus CLI flows with deterministic tests
- [x] run at least 3 review passes and fix findings
- [x] append wrap-up notes for completed slices

## Next ideas
- [x] export benchmark sweeps across multiple tree sizes for chart-ready comparison series
- [ ] add step-by-step trace snapshot export for slide decks or animation tooling
- [ ] generate a Markdown benchmark report with interpretation and embedded artifact links
