# 2026-04-15 suffix-tree DOT export research

## Goal
Add an interview-friendly visualization slice to `suffix-tree-lab` without introducing heavy runtime dependencies.

## Brief findings
- Graphviz DOT is a good portability layer because the project can emit plain text and let users render later with `dot -Tsvg` or similar tools.
- Horizontal layout (`rankdir=LR`) keeps long edge labels more readable than top-down layout for compressed suffix trees.
- Leaf nodes are easier to scan when rendered differently from internal nodes; using `doublecircle` is a lightweight way to make suffix endpoints stand out.
- Suffix trees benefit from keeping edge labels literal in the DOT output because the project is educational and readability matters more than minimizing graph text.
- Optional node annotations for suffix-start offsets help explain why a matched subtree corresponds to multiple occurrence positions.

## Sources consulted
- Graphviz edge and layout docs
- Visualgo and other educational suffix-tree visualizers for labeling/layout ideas
