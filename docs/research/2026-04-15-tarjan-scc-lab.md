# 2026-04-15 Tarjan SCC Lab research

## Goal
Add a new advanced graph-algorithms portfolio project that is still compact enough to finish thoroughly in one slice.

## Brief notes
- Tarjan's SCC algorithm is a strong fit because it is a classic linear-time directed-graph algorithm with interview value and real systems relevance.
- The most portfolio-useful outputs are: SCC membership, high-level graph summary, and the condensation DAG that collapses cycles into a DAG.
- A deterministic CLI matters so the project can be demoed and tested easily from JSON fixtures.

## Implementation choice
Build a Python CLI that:
1. loads adjacency-list or edge-list JSON
2. computes SCCs with Tarjan's DFS/index/low-link technique
3. emits SCC summaries and condensation DAG JSON
4. includes a short text explanation mode for quick interview demos
