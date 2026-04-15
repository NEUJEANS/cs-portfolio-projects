# 2026-04-15 Research — KD-Tree Spatial Search Lab

## Why this project
The repo already covers many classic data structures and distributed-systems labs. A KD-tree adds computational geometry and spatial indexing without overlapping too heavily with the quadtree project.

## Compact design notes
- Build by alternating split axes (`x`, then `y`) and choosing the median point at each level.
- Range queries prune subtrees when the query rectangle does not cross the split plane.
- Nearest-neighbor search descends toward the likely side first, then backtracks only if the splitting plane is close enough to beat the best-so-far distance.
- Deterministic tie-breaking matters for tests and reproducible CLI output.

## Research note
Attempted external web search for KD-tree references, but the configured search provider hit quota/rate limits during this run. The implementation proceeded from standard algorithm knowledge with conservative scope and explicit tests.
