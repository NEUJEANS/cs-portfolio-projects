# Dependency Graph Planner Refresh — 2026-04-20 — synthetic generator slice

## Short refresh
- A good synthetic workload should exaggerate one or two scheduler tradeoffs clearly enough that the resulting reports are worth discussing in interviews.
- CI pipelines are strongest when they show fan-out/fan-in behavior plus a scarce post-build resource such as a browser lab or image builder.
- Release workflows become interesting when parallel builds feed a serialized signing bottleneck and then a staged canary chain.
- Data pipelines are a natural fit for mixed constraints: warehouse slots, partitioned transforms, and a downstream GPU-bound training task.
- Committed artifacts should be portable, so source labels in Markdown/HTML should stay repo-relative when the input path lives inside the repo.

## Self-test
1. Why generate manifests instead of only hand-authoring them?
   - To broaden the portfolio story quickly while keeping the repo deterministic and maintainable.
2. What makes the release generator different from the CI generator?
   - It emphasizes serialized signing and progressive canary rollout rather than a matrix-style test fan-out.
3. Why normalize repo-local source labels?
   - So committed reports stay portable and do not leak machine-specific absolute paths.
