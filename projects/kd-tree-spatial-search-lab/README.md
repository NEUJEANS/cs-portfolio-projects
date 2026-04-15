# KD-Tree Spatial Search Lab

A compact computational-geometry project that builds a 2D KD-tree for fast spatial lookups over labeled points.

## What it demonstrates
- recursive divide-and-conquer tree construction
- axis-alternating partitioning for 2D points
- rectangle range queries with branch pruning
- nearest-neighbor and k-nearest-neighbor search with backtracking and distance bounds
- reproducible benchmarking versus brute-force search
- clean CLI + JSON input/output for reproducible demos

## Files
- `kd_tree_spatial_search.py` — implementation and CLI
- `sample_points.json` — small demo dataset
- `test_kd_tree_spatial_search.py` — correctness and CLI tests

## Usage
```bash
cd projects/kd-tree-spatial-search-lab
python kd_tree_spatial_search.py sample_points.json nearest 7.8 1.2
python kd_tree_spatial_search.py sample_points.json knearest 7 2 3
python kd_tree_spatial_search.py sample_points.json benchmark --queries 500 --k 3 --seed 7
pytest -q test_kd_tree_spatial_search.py
```

## Input format
Provide a JSON array of points:

```json
[
  {"x": 2, "y": 3, "label": "a"},
  {"x": 5, "y": 4, "label": "b"}
]
```

## Why this is portfolio-worthy
KD-trees show practical algorithm engineering beyond textbook sorting/searching. This project highlights geometric indexing, query pruning, deterministic testing, ranking semantics for k-nearest results, and benchmark-driven performance discussion.

## Future improvements
- support radius / circular range queries
- benchmark larger synthetic point clouds and chart scaling behavior
- extend to higher dimensions or typed payload metadata
