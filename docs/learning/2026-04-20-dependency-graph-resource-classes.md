# Dependency graph planner resource-class refresh — 2026-04-20

## Short refresh
- Renewable resource constraints are different from plain worker caps: a task may be ready in the DAG sense but still blocked on a scarce specialist runner such as a GPU or signing host.
- Deterministic list scheduling still works if readiness checks include both dependency completion and resource-slot availability.
- For a portfolio demo, reporting the queue delay and per-resource utilization matters as much as the makespan because it explains *why* the constrained run slowed down.

## Self-test
1. What should happen on the new `resource_graph.json` example with `3 workers` and `gpu=1`?
   - `gpu-train` and `docs` should start right after `prep`, while `gpu-eval` waits for the single GPU slot and the makespan stretches to `8`.
2. What should happen if the same graph is run with `--resource-capacity gpu=2`?
   - Both GPU tasks can start immediately after `prep`, so the constrained schedule drops back to the unlimited makespan of `6`.
3. What should the report show besides the worker timeline?
   - The active resource caps, per-task resource labels/slots, and a small resource-utilization summary table so the bottleneck is visible without reading raw JSON.
