# pathfinding-visualizer

## Overview
Render shortest paths on ASCII maps using either BFS or A*.

This project is intentionally portfolio-friendly: it demonstrates graph search, heuristics, input validation, weighted traversal costs, CLI design, and test coverage in a compact codebase.

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
- BFS for shortest path by step count
- A* with Manhattan-distance heuristic for efficient weighted search on a 4-direction grid
- rendered ASCII output with path overlay
- summary metrics for visited nodes, path length, and path cost
- no-path handling instead of crashing, with a non-zero exit code for scripting

## Usage
```bash
python3 pathfinding.py map.txt
python3 pathfinding.py map.txt --algorithm astar
```

Example output:
```text
algorithm: astar
visited_nodes: 6
path_found: yes
path_length: 5
path_cost: 5

S.WE
***.
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is a good CS portfolio project
- shows practical graph traversal and heuristic search
- creates a visible, easy-to-demo result from text input
- leaves room for future expansion into animation, diagonal movement, or GUI rendering

## Future Improvements
- animate frontier expansion step-by-step
- support diagonal movement and configurable heuristics
- compare BFS, Dijkstra, and A* on larger benchmark maps
- export rendered results to HTML or image output
