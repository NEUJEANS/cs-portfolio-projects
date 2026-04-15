# 2026-04-15 tarjan-scc review pass 1

## Focus
Algorithm summary correctness.

## Issue found
- `acyclic` incorrectly treated a singleton node with a self-loop as acyclic.

## Fix
- tracked per-component self-loop metadata
- changed summary logic to count singleton self-loops as cyclic components
- added regression coverage for the self-loop case
