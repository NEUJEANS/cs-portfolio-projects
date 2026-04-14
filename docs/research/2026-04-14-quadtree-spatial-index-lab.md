# Quadtree Spatial Index Lab Research

## Why this project
The repository already covers many core data-structure and systems topics, but it does not yet include a spatial index. A point-region quadtree adds geometric partitioning, range search, and nearest-neighbor querying — all interview-friendly topics that are easy to demo.

## Practical design notes
- Use an axis-aligned rectangular boundary for each node.
- Subdivide only when a leaf exceeds capacity and depth allows it.
- Keep insertion deterministic by routing each point to exactly one child after subdivision.
- Support rectangle range queries efficiently by pruning non-intersecting quadrants.
- Support nearest-neighbor search by visiting candidate quadrants in distance order and pruning quadrants whose minimum possible distance already exceeds the current best.

## Portfolio angle
This project demonstrates:
- geometric data structures
- recursive divide-and-conquer design
- pruning for query performance
- careful handling of boundary conditions and duplicates
- test-driven algorithm work with realistic query examples

## Planned slice
Ship a polished Python lab with:
1. point-region quadtree implementation
2. rectangle range query
3. nearest-neighbor search
4. CLI demo using JSON point sets
5. README with architecture notes and sample commands
