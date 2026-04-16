# 2026-04-16 learning refresh — graph-routing-negative-cycle-lab

## Brief research takeaway
- Bellman-Ford stays portfolio-worthy because it doubles as both a shortest-path solver and a negative-cycle detector for routing-style graphs.
- Johnson's algorithm is a strong companion because it converts a single-source Bellman-Ford pass into all-pairs shortest paths without requiring non-negative input edges up front.
- A good student-facing demo should make the iteration states and failure mode visible, not just print final distances.

## Self-test
1. Why can't Dijkstra run directly on graphs with negative edges?
   - Because greedily finalizing a node can become invalid after a later negative-weight relaxation.
2. What extra signal proves a reachable negative cycle in Bellman-Ford?
   - Any successful relaxation on the extra pass after `|V|-1` iterations.
3. Why does Johnson add a super-source?
   - To compute a potential for every node, even in disconnected graphs, before reweighting edges.
4. What must remain true after Johnson reweighting?
   - Every reweighted edge cost must be non-negative if no negative cycle exists.
