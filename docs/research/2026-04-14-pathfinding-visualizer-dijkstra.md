# Pathfinding visualizer: Dijkstra baseline research

Date: 2026-04-14

## Goal
Strengthen `pathfinding-visualizer` by adding a weighted shortest-path baseline that makes the portfolio story clearer.

## Notes
- BFS is correct for minimizing edge count on unweighted graphs, but it is not cost-optimal once tiles have different traversal costs.
- Dijkstra is the standard weighted shortest-path baseline for non-negative edge weights and gives an easy-to-explain correctness story.
- A* should match Dijkstra's optimal path cost when its heuristic is admissible and consistent.
- On a 4-direction grid with non-negative movement costs, Manhattan distance is a sensible heuristic signal for A*; it should usually explore fewer nodes than Dijkstra while preserving optimality.

## Slice choice
Add `--algorithm dijkstra` beside existing BFS and A* support, then test that:
1. BFS can return a lower-step but higher-cost route on weighted maps.
2. Dijkstra and A* agree on optimal weighted cost.
3. A* does not visit more nodes than Dijkstra on the representative weighted test map.

## Research note
Web-search quota was unavailable during this run, so these notes are based on standard pathfinding references and algorithm knowledge rather than live citation capture.
