# KD-Tree Spatial Search Lab

A compact computational-geometry project that builds a 2D KD-tree for fast spatial lookups over labeled points.

## What it demonstrates
- recursive divide-and-conquer tree construction
- axis-alternating partitioning for 2D points
- rectangle range queries with branch pruning
- circular radius queries with distance-sorted results and optional result caps
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
python3 kd_tree_spatial_search.py sample_points.json nearest 7.8 1.2
python3 kd_tree_spatial_search.py sample_points.json knearest 7 2 3
python3 kd_tree_spatial_search.py sample_points.json radius 7 2 3 --limit 2
python3 kd_tree_spatial_search.py sample_points.json benchmark --queries 500 --k 3 --seed 7
python3 -m pytest -q test_kd_tree_spatial_search.py
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
KD-trees show practical algorithm engineering beyond textbook sorting/searching. This project highlights geometric indexing, query pruning, deterministic testing, circular-vs-rectangular query semantics, ranking semantics for k-nearest and radius results, and benchmark-driven performance discussion.

## Example artifact
- `docs/artifacts/kd-tree-radius-query-sample.json` - committed sample output for a radius-3 query centered at `(7, 2)` with the top 3 matches

## Future improvements
- benchmark larger synthetic point clouds and chart scaling behavior
- extend to higher dimensions or typed payload metadata
- add optional SVG scatterplot exports for README-ready visual demos
