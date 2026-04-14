# 2026-04-14 pathfinding visualizer upgrade research

## Goal
Strengthen `pathfinding-visualizer` so it reads like a real CS portfolio project rather than a single BFS demo.

## Notes used for this slice
- BFS is still the right baseline for shortest path by number of steps on an unweighted grid.
- A* with Manhattan distance is a good fit for a 4-direction grid because the heuristic is simple and admissible.
- Adding a weighted traversable tile makes the difference between step count and path cost visible, which helps justify having both BFS and A* in the project.
- Input validation matters for portfolio quality: empty maps, non-rectangular maps, unsupported tiles, and missing start/end markers should fail cleanly.
- A compact CLI with algorithm selection and testable formatted output is more demo-friendly than printing only a raw rendered map.

## Planned improvement
Upgrade the project with:
1. map parsing/validation
2. BFS and A* search modes
3. weighted tile support (`W`)
4. summary metrics and no-path reporting
5. stronger tests and README examples
