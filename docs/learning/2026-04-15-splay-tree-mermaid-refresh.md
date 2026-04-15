# Splay Tree Mermaid Export Refresh — 2026-04-15

## Goal
Add a lightweight Mermaid export path for `splay-tree-lab` access traces so the project can produce browser-friendly visuals without requiring Graphviz.

## Quick refresh
- Mermaid `flowchart TD` is the simplest portable option for binary-tree snapshots.
- Stable node identifiers should avoid punctuation and whitespace; tree keys can be embedded in prefixed ids.
- Styling should be emitted after nodes/edges with `classDef` and `class` lines so root and highlighted access keys remain obvious.
- Null children do not need placeholder nodes in Mermaid; omitting them keeps the diagram compact and readable.

## Self-test
- Can I emit a deterministic top-down tree from the existing in-memory structure? Yes: DFS over left/right children in stable order.
- Can I preserve root emphasis separately from requested-key highlighting? Yes: emit `root` and `highlight` classes independently.
- Can the CLI mirror the existing DOT flow cleanly? Yes: add optional `--before-mermaid` and `--after-mermaid` flags to the `trace` subcommand.
