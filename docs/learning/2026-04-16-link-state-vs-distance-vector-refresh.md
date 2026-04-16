# 2026-04-16 link-state vs distance-vector refresh

## Quick refresh
- Link-state routers flood link-state advertisements so every router reconstructs the same graph and then runs shortest-path locally.
- Distance-vector routers exchange only neighbor cost tables, so convergence depends on iterative propagation of better or worse estimates.
- Count-to-infinity is primarily a distance-vector failure mode because routers can keep trusting stale next-hop information after a failure.
- Link-state avoids that specific loop by recomputing from fresh topology state once updated LSAs are flooded.

## Self-test
1. If one link fails, which model needs fresh graph flood vs repeated cost propagation?
   - Link-state: fresh graph flood.
   - Distance-vector: repeated cost propagation.
2. Why can distance-vector need more rounds after a failure?
   - Routers only know neighbor advertisements, so incorrect costs can be revised gradually.
3. What should a good portfolio comparison expose?
   - steady-state convergence summary
   - optional failure event summary
   - mode/update-strategy metadata for the distance-vector side
