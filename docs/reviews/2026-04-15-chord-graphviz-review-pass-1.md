# Chord Graphviz review pass 1

## Focus
Functional completeness and CLI surface.

## Findings
1. Needed a dedicated export surface instead of burying DOT only inside the demo payload.
2. README usage had to show at least one direct `graphviz` command so the slice is runnable.

## Fixes applied
- Added `export_graphviz()` plus `graphviz` CLI mode selection.
- Added README examples for route and stabilization DOT export.
