# 2026-04-14 pathfinding visualizer Dijkstra review - pass 1

## Focus
Algorithm correctness for weighted shortest-path behavior.

## Findings
- The first weighted test map proved Dijkstra and A* produced the same optimal cost, but it did not reliably show A* exploring fewer nodes.

## Fixes
- Replaced the comparison test with a larger representative grid where Dijkstra visits 16 nodes and A* visits 15 while preserving the same optimal cost.
- Kept the smaller `SWWE` map as the BFS-vs-weighted-cost regression test.

## Validation
- `python3 -m unittest discover -s projects/pathfinding-visualizer -p 'test_*.py'` -> pass
