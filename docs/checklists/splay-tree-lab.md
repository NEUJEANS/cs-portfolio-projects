# splay-tree-lab checklist

## Status
- [x] vertical slice 8 complete

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
- [x] add step-by-step trace snapshot export for slide decks or animation tooling
- [x] generate a Markdown benchmark report with interpretation and embedded artifact links
- [ ] render the Mermaid benchmark report into checked-in SVG/PNG assets for portfolio sites that do not support Mermaid natively

## Trace step-snapshot export slice (2026-04-16 12:29 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current trace tooling for the weakest unfinished portfolio-visualization gap
- [x] skip web research because per-step snapshot export is a direct extension of the existing trace workflow and README backlog
- [x] do a short Python `Path`/filename self-test for deterministic step snapshot names
- [x] update checklist/docs so the slice is resumable
- [x] add optional per-step structured trace snapshot export plus a manifest for replayable demos
- [x] commit sample trace-step artifacts for portfolio walkthroughs
- [x] extend automated coverage for structured snapshots, manifest export, and CLI behavior
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Benchmark report slice (2026-04-16 12:47 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the current benchmark tooling for the weakest unfinished portfolio-reporting gap
- [x] skip web research because the README backlog already pointed to Markdown report export as the next direct extension
- [x] skip language/tool refresh because the existing benchmark-series CLI already covered the core JSON/CSV path and only needed a focused report-rendering extension
- [x] update checklist/docs so the slice is resumable
- [x] add a `benchmark-report` CLI that renders a Markdown benchmark report with Mermaid charts and embedded artifact links
- [x] commit a generated benchmark report artifact for portfolio reuse
- [x] extend automated coverage for Markdown rendering, artifact links, and CLI output
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
