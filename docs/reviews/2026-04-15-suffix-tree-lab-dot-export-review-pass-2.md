# 2026-04-15 suffix-tree-lab DOT export review pass 2

## Focus
Determinism, renderability, and code health.

## Findings
1. DOT output should remain stable across runs so generated artifacts are diff-friendly.
2. The new export path should be syntax-checked outside pytest collection.

## Fixes
- kept edge traversal sorted by edge label so node/edge emission order is deterministic.
- validated the module and tests with `python -m py_compile` and inspected a sample DOT export.
