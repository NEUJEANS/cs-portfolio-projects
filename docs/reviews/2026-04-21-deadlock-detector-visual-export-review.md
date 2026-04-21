# Deadlock detector visual export review log

## Pass 1, wait-for edge readability audit
- Checked whether the new wait-for SVG stays readable for two-process deadlocks as well as longer cycles.
- Found a visual regression: bidirectional waits were being drawn on the same straight line, so a `P1 -> P2 -> P1` cycle collapsed into one overlapping stroke.
- Fix: render reverse-direction wait edges as curved quadratic paths so two-node deadlocks remain visible in exported SVG and HTML artifacts.

## Pass 2, allocation edge-label clarity audit
- Checked the resource-allocation SVG for crossed request edges and whether the arrows visually match the edge semantics.
- Found two readability issues: opposing blocked-request labels could land on the same midpoint, and held-resource edges used a blue stroke with a generic slate arrowhead.
- Fix: stagger request-label vertical offsets based on edge direction and add a dedicated blue arrow marker for held-resource edges.

## Pass 3, docs and artifact audit
- Checked that the new export flow is actually resumable from the repo without reading source code.
- Found missing project-level guidance and committed samples for the new visual outputs.
- Fix: update the project README with `--svg-out` and `--html-out` examples, refresh the deadlock checklist, add research/learning notes, and commit deterministic sample SVG, HTML, and JSON artifacts for both wait-for and allocation demos.
