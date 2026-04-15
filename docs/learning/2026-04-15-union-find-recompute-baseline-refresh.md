# Union-Find recompute baseline refresh — 2026-04-15

## Why this refresh
The next strongest portfolio improvement for `union-find-network-lab` was not another DSU feature, but a baseline that makes the DSU advantage visible. The comparison target is a deliberately naive but honest strategy: after each new edge, recompute connected components from the full graph with BFS.

## Refreshed ideas
- union-find is ideal for incremental connectivity updates because it stores component structure compactly and updates it per edge
- a BFS/DFS recomputation baseline is still useful because it is easy to explain in interviews and acts as a correctness cross-check
- if both strategies consume the exact same random edge stream, the final largest-component and component-count results should match even when runtimes differ wildly
- cumulative checkpoint timing makes the story easier to visualize than a single total time number

## Tiny self-test
1. If `a` and `c` are already connected through `a-b-c`, adding `a-c` should count as a cycle edge for both the DSU path-check view and the recomputation baseline.
2. A BFS component recomputation can derive:
   - component count
   - largest component size
   - whether a component is cyclic from `edges >= nodes`
3. For a fair benchmark comparison, generate one seeded edge list first, then replay it through both strategies.

## Result
Implemented the comparison using:
- seeded shared edge generation
- `graph_path_exists(...)` for baseline cycle detection before edge insertion
- `recompute_graph_stats(...)` for full-component recomputation after every edge
- checkpoint artifacts that drive a committed SVG comparison chart
