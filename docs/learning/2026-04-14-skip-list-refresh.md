# Learning Refresh - Skip List KV Lab

## Quick refresh
- Search starts from the highest populated level and moves right while the next node key is still below target.
- Insert/delete track predecessors (`update[]`) at every level so pointer rewiring is `O(level)` after the search phase.
- Expected complexity is logarithmic because only a fraction of nodes appear in higher levels.
- Range queries can seek to the lower bound first, then stream forward on level 0.

## Self-test
1. Why keep an `update` array during insert/delete?
   - To remember the predecessor node at each level for pointer rewiring.
2. Why does a skip list need at least a sentinel/head node?
   - It gives every level a consistent starting point and avoids many edge-case branches.
3. What makes the implementation portfolio-friendly?
   - It demonstrates randomized structure design, sorted indexing, and testable ordered queries without hiding behind library maps.
