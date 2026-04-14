# pathfinding-visualizer

## Overview
Render shortest paths on ASCII maps using BFS, Dijkstra, or A*.

This project is intentionally portfolio-friendly: it demonstrates graph search, weighted shortest paths, admissible heuristics, input validation, CLI design, and test coverage in a compact codebase.

## Stack
- Python 3
- standard library only

## Map Format
- `S` start
- `E` end
- `.` normal traversable tile with cost `1`
- `W` weighted traversable tile with cost `3`
- `#` wall

## Features
- rectangular-map validation with clear error messages
- BFS for shortest path by step count on unweighted maps
- Dijkstra for optimal weighted shortest paths
- A* with Manhattan-distance heuristic for efficient weighted search on a 4-direction grid
- rendered ASCII output with path overlay
- summary metrics for visited nodes, path length, and path cost
- no-path handling instead of crashing, with a non-zero exit code for scripting

## Usage
```bash
python3 pathfinding.py map.txt
python3 pathfinding.py map.txt --algorithm dijkstra
python3 pathfinding.py map.txt --algorithm astar
```

Example output:
```text
algorithm: dijkstra
visited_nodes: 7
path_found: yes
path_length: 5
path_cost: 5

SWWE
****
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is a good CS portfolio project
- shows practical graph traversal plus weighted shortest-path algorithms
- creates a visible, easy-to-demo result from text input
- makes it easy to explain when BFS is insufficient and why Dijkstra/A* are better on weighted grids

## Future Improvements
- animate frontier expansion step-by-step
- support diagonal movement and configurable heuristics
- compare BFS, Dijkstra, and A* on larger benchmark maps
- export rendered results to HTML or image output
