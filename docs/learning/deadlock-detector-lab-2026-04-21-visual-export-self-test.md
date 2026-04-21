# Deadlock detector visual export self-test

## Quick refresh
- Wait-for graphs are process-to-process graphs, so the highest-signal visual is the cycle plus any extra incoming wait edges.
- Resource-allocation graphs are bipartite: resources point to holders, processes point to requested resources.
- For static artifacts, deterministic layout matters more than perfect graph aesthetics because committed screenshots and diffs should stay stable.

## Self-test
1. **What should the wait-for SVG emphasize first?**
   - The processes in the cycle.
   - The directed edges that close the deadlock loop.
   - Any extra waiting edges as secondary context.

2. **What should the resource-allocation export show for blocked states?**
   - Which resources are currently available.
   - Which resources are already held by each process.
   - Which outstanding requests are still blocked, including the shortage amount when possible.

3. **Why keep the HTML report self-contained?**
   - It is easy to open from the repo or attach to a portfolio.
   - It avoids runtime dependencies.
   - It keeps deterministic exported artifacts simple to diff and regenerate.

## Practical rule for this slice
Prefer diagrams that explain the deadlock story in one glance over diagrams that try to encode every possible metric at once.
