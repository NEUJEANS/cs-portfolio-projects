# 2026-04-15 Tarjan SCC refresh and self-test

## Refresh
- Tarjan assigns each node a DFS discovery index and a low-link value.
- A node starts a strongly connected component exactly when its low-link equals its discovery index.
- Back edges to nodes currently on the DFS stack can lower the current node's low-link.
- The condensation graph is always acyclic because each SCC is collapsed into a single meta-node.

## Self-test
- If DFS reaches `A -> B -> C -> A`, all three should end up in one SCC.
- If there is only `C -> D` between two SCCs and no path back, the condensation DAG should contain one directed edge between the two components.
- In a DAG, every SCC should be a singleton.
