# Dependency Graph Planner Review Pass 1

## Focus
Algorithm correctness and deterministic behavior.

## Issues found
1. Ready tasks were appended to a FIFO queue, which could make topological output depend on discovery order instead of a stable global lexical tie-break.
2. Critical-path extraction treated every node as a candidate because the initial filter was too loose.

## Fixes made
- switched the ready queue to a min-heap for deterministic global ordering
- tightened critical-path extraction to walk only zero-slack nodes with matching earliest-start/finish boundaries
- added a regression test for lexical tie-breaking
