# Dependency graph planner refresh — 2026-04-20 — stress benchmark slice

## Short refresh
- A synthetic stress DAG should exaggerate one scheduler tradeoff clearly enough that a benchmark table becomes interview material, not just more noise.
- Seeded pseudo-random generation is a good fit for committed portfolio artifacts because it broadens workload coverage while keeping exports reproducible.
- The critical-path duration is a clean lower bound for a DAG schedule, so comparing heuristic makespans against it is more informative than comparing only against other heuristics.
- Dashboard summary cards need their own metric-specific winner selection; reusing the top aggregate leader can silently misreport secondary metrics.
- Artifact regeneration matters after benchmark-schema changes because JSON/CSV/Markdown/HTML outputs all encode the same reporting contract.

## Self-test
1. Why store a seed in generated stress manifest metadata?
   - So the benchmark case is reproducible and reviewers can regenerate the same workload exactly.
2. Why include both delta and ratio versus the critical-path lower bound?
   - Delta shows the raw gap, while ratio makes workloads of different absolute sizes easier to compare.
3. Why add a dedicated dashboard-summary regression test?
   - Because the leaderboard winner for one metric is not guaranteed to be the winner for another, and the HTML summary should not accidentally reuse the wrong strategy.
