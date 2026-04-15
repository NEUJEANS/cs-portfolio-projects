# Pathfinding compare-mode research — 2026-04-15

## Why this slice
The project already solved weighted grids, but it still needed a stronger demo surface. A compare mode lets one command show where BFS is cheaper in steps yet worse in weighted cost, while Dijkstra and A* still agree on the optimum.

## Brief research notes
- Dijkstra's algorithm is effectively A* with a zero heuristic, so it explores by known distance from the start only.
- With an admissible heuristic like Manhattan distance on a 4-direction grid, A* should expand the same or fewer nodes than Dijkstra while preserving optimal cost.
- That makes `visited_nodes` and `optimal_cost_match` good lightweight portfolio metrics for a compare command.

## Implementation direction
- Keep the existing single-algorithm CLI intact.
- Add a compare mode that reuses the same search functions instead of introducing a separate benchmark framework.
- Print each algorithm's rendered path plus metrics so the feature stays easy to demo in screenshots or terminal recordings.
