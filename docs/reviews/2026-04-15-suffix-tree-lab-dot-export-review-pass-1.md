# 2026-04-15 suffix-tree-lab DOT export review pass 1

## Focus
API and visualization output sanity check.

## Findings
1. The initial `--show-suffix-starts` export only annotated non-root nodes, which made the full suffix coverage harder to explain from the first node.

## Fixes
- updated DOT export so the root label includes the full suffix-start list when annotations are enabled.
- reran the project test file after the fix.
