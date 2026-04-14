# Weighted pathfinding refresh and self-test

Date: 2026-04-14

## Quick refresh
- Dijkstra uses a priority queue ordered by current best known distance.
- A* uses `g(n) + h(n)` priority where `g` is the accumulated path cost and `h` is a heuristic estimate to the goal.
- If `h(n)=0`, A* reduces to Dijkstra.
- For correctness with Dijkstra/A*, edge weights must be non-negative.

## Self-test
- Q: Why can BFS be wrong on a weighted grid?
  - A: It minimizes number of steps, not total traversal cost.
- Q: What makes Manhattan distance useful here?
  - A: On a 4-neighbor grid it estimates remaining distance without overfocusing on walls, giving A* directional guidance.
- Q: How can one implementation support both Dijkstra and A*?
  - A: Share the weighted frontier loop and switch whether heuristic cost contributes to priority.
