# extendible-hashing-lab phase-split probe summaries self-test — 2026-04-21

## Quick refresh
- insertion cost in linear probing tracks the same empty-slot search path as an unsuccessful lookup
- successful lookups often look better than misses, especially after clustering and tombstones stretch probe runs
- averages alone can hide the worst recruiter-demo moments, so p50/p95/max summaries are worth exporting
- resumable portfolio artifacts should tell the story consistently across JSON, Markdown, HTML, and CSV

## Self-test
1. **Q:** Why keep both `lookup_probe_breakdown` and `phase_probe_breakdown`?
   **A:** Lookup hit/miss explains user-facing query cost, while phase splits show which workload stage (puts, gets, deletes) generated the pressure.
2. **Q:** Why export phase data to CSV too if JSON already has it?
   **A:** The repo’s artifact bundle is meant for quick plotting and recruiter-friendly inspection, and CSV is the lowest-friction format for follow-up charts.
3. **Q:** What should stand out in the clustering scenario after this slice?
   **A:** Miss lookups should stay worse than hits, and the `gets` phase should visibly look more expensive than the calmer scenarios.
