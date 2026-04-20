# Dependency Graph Planner Refresh — 2026-04-20 multi-capacity comparison slice

## Quick refresh
- The sample graph still has total work `9` and unlimited layered makespan `8`.
- With `1` worker, the deterministic critical-first scheduler must serialize `unit` before `package`, so the run stretches to makespan `9` and `package` waits `2` time units.
- With `2` or `3` workers, `unit` and `package` can start together at time `5`, so the makespan returns to the unlimited bound of `8`.

## Self-test before editing
- Expected comparison summary: `1 worker → 9, 2 workers → 8, 3 workers → 8`.
- Expected comparison table deltas vs unlimited: `1, 0, 0`.
- Expected idle capacity: `0` for `1` worker, then non-zero for `2+` workers because the graph is dependency-bound rather than capacity-bound.
