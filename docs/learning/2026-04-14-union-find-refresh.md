# Refresh — union-find / Python implementation

## Quick refresh
- `find` should compress paths so repeated lookups flatten trees.
- `union` should attach the shallower tree to the deeper one.
- Component metadata can live on roots only and be merged during successful unions.
- A redundant edge creates a cycle when both endpoints already share a root.

## Self-test
1. Why does path compression improve future `find` calls?
   - It rewrites traversed nodes to point directly at the root.
2. Why keep size/edge metadata on roots?
   - Only roots survive merges, so root-local metadata is easy to aggregate correctly.
3. How can cycle detection piggyback on DSU?
   - If `find(a) == find(b)` before union, the new edge is redundant inside the same component.
