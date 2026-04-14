# 2026-04-14 pathfinding refresh and self-test

## Quick refresh
- `collections.deque` is the right queue for BFS.
- `heapq` is the standard-library priority queue for A*.
- Manhattan distance `abs(r1-r2) + abs(c1-c2)` is the standard heuristic for 4-direction grid movement.
- A* becomes more meaningful when traversable cells can have different costs.

## Tiny self-test
Question: On a 4-direction grid, why is Manhattan distance a safe A* heuristic?

Answer: It never overestimates the minimum number of moves remaining because each legal move changes row or column distance by at most 1, so the heuristic is admissible. That keeps A* optimal when edge costs are non-negative.

## Practical reminder for implementation
If weighted tiles are added, BFS still minimizes step count, not total movement cost. That difference should be explicit in tests and README examples.
