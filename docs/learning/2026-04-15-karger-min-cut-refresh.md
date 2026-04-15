# 2026-04-15 Karger min cut refresh

## Quick refresh
- Karger's algorithm repeatedly contracts a uniformly random edge until only two supernodes remain.
- The number of parallel edges left between those supernodes is the cut size reported by that trial.
- A single run succeeds with probability at least `2 / (n * (n - 1))` for an `n`-vertex graph, so repeated trials are essential.
- Self-loops must be discarded after each contraction, while parallel crossing edges must be preserved.

## Self-test
1. Why can the graph become a multigraph during contraction?
2. Why do repeated trials improve confidence without changing one trial's logic?
3. Why would keeping self-loops corrupt the result?

## Answers
1. Distinct crossing edges can collapse onto the same pair of supernodes after contraction.
2. Each trial is another independent chance to avoid contracting a true min-cut edge.
3. Self-loops would count internal edges that should not contribute to the remaining cut.
