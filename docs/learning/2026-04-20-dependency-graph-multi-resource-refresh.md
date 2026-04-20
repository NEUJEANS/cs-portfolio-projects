# Dependency graph planner multi-resource refresh — 2026-04-20

## Short refresh
- A task can be dependency-ready but still blocked if it needs *multiple* scarce resources simultaneously and even one of them is unavailable.
- Reporting only makespan is not enough for this slice; the useful story is demand vectors, concrete slot allocations, queue delay, peak concurrent usage, and reserved-capacity totals.
- Backwards compatibility matters for portfolio projects too: keeping `resource_class` working avoids breaking earlier manifests while `resources` unlocks richer cases.

## Self-test
1. What should happen on `multi_resource_graph.json` with `3 workers`, `browser-lab=2`, `gpu=1`, and `signing=1`?
   - `browser-matrix` and `gpu-train` can start after `prep`, but `cross-platform-cert` must wait until both a browser-lab slot and the GPU are simultaneously free, stretching the schedule to `10`.
2. What should happen if the browser-lab capacity is overridden to `3`?
   - `cross-platform-cert` can start earlier, but it still waits on the GPU, so the makespan improves only to `9` instead of snapping all the way back to the unlimited bound.
3. What should the report make obvious?
   - That `cross-platform-cert` is the multi-resource bottleneck, and that the browser-lab and GPU summaries explain the wait without reading raw code.
