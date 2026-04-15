# Pathfinding compare-mode refresh — 2026-04-15

## Quick refresher
- BFS minimizes edge count, not weighted path cost.
- Dijkstra minimizes total cost for non-negative edge weights.
- A* uses `f(n) = g(n) + h(n)` and remains optimal when `h(n)` does not overestimate the remaining cost.

## Self-test
1. On a grid with expensive `W` tiles, can BFS still return a path with fewer steps but higher cost? Yes.
2. If Manhattan distance is admissible on a 4-neighbor grid, should A* ever beat Dijkstra on total path cost? No, only on search effort.
3. What should compare mode highlight for a portfolio demo? Path cost, path length, visited nodes, and whether an algorithm matched the optimal weighted cost.
