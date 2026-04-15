# 2026-04-15 treap cross-tree benchmark refresh

## Quick refresh
- Dynamic imports are the cleanest way to reuse sibling project modules without converting the repo into one package.
- For AVL/red-black lookup comparisons, a read-only manual traversal is enough; no need to modify those projects.
- For splay, benchmark successful lookups through `find()` so the self-adjusting behavior and rotation cost are visible.
- CSV export should stay deterministic and chart-ready so the run can produce a reusable artifact.

## Self-test
- Why not use wall-clock timing? Because deterministic structural metrics and comparison counts are much more stable in CI and better for resumable repo artifacts.
- Why separate build seed and query seed? To keep insertion shape deterministic while allowing the query workload to vary independently.
