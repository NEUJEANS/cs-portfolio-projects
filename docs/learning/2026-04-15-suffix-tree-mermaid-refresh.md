# 2026-04-15 — Suffix Tree Mermaid Export Refresh

## Goal
Add a lightweight diagram export that renders nicely in GitHub-friendly Markdown without depending on a local Graphviz installation.

## Quick refresh
- Mermaid `flowchart LR` is a good fit for small educational tree diagrams.
- Node labels should stay short and escaped carefully; line breaks can be represented with `<br/>`.
- Reusing the same traversal order as DOT keeps the two export modes comparable in tests and screenshots.
- Mermaid edge labels are expressive enough for compressed suffix-edge substrings, which preserves the educational value of the tree.

## Self-check
- Keep leaf styling simple and deterministic.
- Make sure suffix-start annotations stay optional, just like the DOT export.
- Verify the CLI exposes Mermaid export as a first-class command rather than a hidden flag.
