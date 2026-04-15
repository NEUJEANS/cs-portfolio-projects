# 2026-04-15 network-flow refresh

## Quick refresh
- Max flow pushes capacity through a directed graph from `source` to `sink` while respecting per-edge capacity constraints.
- Edmonds-Karp is Ford-Fulkerson with BFS over the residual graph, giving a deterministic shortest-augmenting-path choice.
- Residual reverse edges are essential because later augmenting paths may need to cancel part of an earlier route.
- After the algorithm stops, nodes still reachable from the source in the residual graph define a minimum cut.

## Self-test
1. Why does Edmonds-Karp use BFS instead of arbitrary path choice?
   - To bound the number of times edges can become critical and achieve `O(V * E^2)` worst-case complexity.
2. Why keep reverse residual capacity?
   - To reroute previously assigned flow when a better augmenting path is discovered later.
3. How do you extract a min cut at the end?
   - Run one final reachability search in the residual graph from the source and split nodes into reachable vs unreachable.
