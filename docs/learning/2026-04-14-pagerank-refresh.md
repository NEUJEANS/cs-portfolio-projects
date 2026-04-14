# 2026-04-14 PageRank Refresh + Self-Test

## Quick refresh
- Represent the web/link structure as a directed graph.
- Initialize every node with equal probability mass `1 / N`.
- Each iteration distributes rank through outgoing links and adds teleportation mass `(1 - damping) / N`.
- Dangling nodes contribute their current rank evenly to all nodes.
- Stop early when the L1 delta between iterations drops below tolerance.

## Self-test
1. Why are dangling nodes special?
   - They have no outgoing edges, so their rank mass must be redistributed or the model leaks/traps probability.
2. What should the sum of all PageRank scores be after each iteration?
   - Approximately `1.0`.
3. What does a smaller convergence delta mean?
   - The score vector changed less between iterations, so the algorithm is stabilizing.
