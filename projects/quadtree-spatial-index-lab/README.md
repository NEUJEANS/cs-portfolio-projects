# Quadtree Spatial Index Lab

A Python point-region quadtree that indexes 2D points for fast rectangle range queries and nearest-neighbor lookups.

## Why this project matters
Spatial indexing is a practical CS topic that shows up in map search, game worlds, collision systems, and analytics dashboards. This lab demonstrates recursive partitioning, geometric pruning, and algorithmic testing in a small but interview-friendly package.

## Features
- point-region quadtree with configurable node capacity and max depth
- rectangle range query with quadrant pruning
- nearest-neighbor search ordered by bounding-box distance
- JSON-backed CLI demo for local experimentation
- tree statistics command for showing index shape and subdivision depth
- focused tests for insertion, boundaries, range search, nearest lookup, and stats output

## Files
- `quadtree_spatial_index.py` - implementation + CLI
- `sample_points.json` - demo campus-style points
- `test_quadtree_spatial_index.py` - pytest suite

## Usage
Run a rectangle range query:

```bash
python3 projects/quadtree-spatial-index-lab/quadtree_spatial_index.py \
  projects/quadtree-spatial-index-lab/sample_points.json \
  --boundary 0 0 10 10 \
  range --area 0 0 5 5
```

Find the nearest point to a target:

```bash
python3 projects/quadtree-spatial-index-lab/quadtree_spatial_index.py \
  projects/quadtree-spatial-index-lab/sample_points.json \
  --boundary 0 0 10 10 \
  nearest --target 8.4 8.5
```

Inspect tree shape statistics:

```bash
python3 projects/quadtree-spatial-index-lab/quadtree_spatial_index.py \
  projects/quadtree-spatial-index-lab/sample_points.json \
  --boundary 0 0 10 10 \
  --capacity 2 \
  stats
```

Run tests:

```bash
python3 -m unittest -q projects/quadtree-spatial-index-lab/test_quadtree_spatial_index.py
```

## Architecture notes
1. `Rectangle` handles containment, intersection, and minimum-distance pruning.
2. `Quadtree` stores points in leaves until capacity is exceeded, then subdivides into four child rectangles.
3. Range queries skip non-overlapping quadrants.
4. Nearest-neighbor search visits quadrants in increasing bounding-box distance order so pruning becomes effective early.

## Future improvements
- k-nearest-neighbor queries
- circular radius search
- visualization output for quadrant splits
- bulk-loading heuristics for large datasets
