# Dependency graph planner research — 2026-04-20 — multi-resource demands

## Brief research / terminology check
- The scheduling vocabulary for this slice is still in the resource-constrained project scheduling family: tasks have precedence constraints plus renewable shared resources with limited capacities.
- The new capability is best described as per-task multi-resource demand vectors rather than a single optional resource label, because one task can now require multiple renewable resources at the same time.
- For this portfolio project, a deterministic heuristic scheduler plus transparent reports is a better fit than a heavyweight optimal solver: the code stays readable while still showing realistic CI/release bottlenecks.

## Practical takeaway for this slice
- Keep `resource_class` as a backwards-compatible shorthand for simple manifests.
- Add `resources` for richer tasks that need multiple capacities simultaneously.
- Make the docs and committed artifacts visibly prove the new behavior, otherwise the feature is too easy to miss.
