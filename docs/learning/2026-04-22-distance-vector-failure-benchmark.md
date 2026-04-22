# Distance Vector Failure Benchmark Refresh

- Date: 2026-04-22
- Project: `distance-vector-routing-lab`

## Quick refresh
- steady-state shortest paths are less interesting here than post-failure reconvergence behavior
- the watched route should capture three moments clearly: first change, first unreachable state, and worst finite metric before stabilization
- periodic and triggered runs both include a final settling step, so the benchmark should report both total rounds and the last round where the watched route actually changed

## Self-test
Q: Why track `max_finite_cost_seen` separately from `max_cost_seen`?
A: Because `max_cost_seen` always reaches infinity once a failed route becomes unreachable, which hides the real count-to-infinity escalation. `max_finite_cost_seen` preserves the interesting transient peak.
