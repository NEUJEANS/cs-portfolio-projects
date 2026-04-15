# Tarjan vs Kosaraju refresh

## Quick refresh
- Tarjan computes SCCs in one DFS using discovery indexes, low-link propagation, and a stack of active nodes.
- Kosaraju does two DFS passes: first to record finish order on the original graph, then DFS on the transposed graph in reverse finish order.
- Both run in O(V + E), but Kosaraju needs the transpose graph and a second traversal.

## Self-test
1. Why does reverse finish order matter in Kosaraju?
   - Because it starts the transpose traversal from SCCs that finish last in the original graph, preventing one SCC traversal from leaking into another.
2. What extra structure does Kosaraju need compared with Tarjan?
   - A transpose adjacency map plus the finish-order stack/list.
3. How can the project keep outputs deterministic across both algorithms?
   - Sort nodes within each component and sort the final component list with the same ranking rule already used by Tarjan.
