# Two-phase commit lab catalog refresh + self-test — 2026-04-20

## Quick refresh
- a bundle landing page should make comparison cheaper than opening four separate reports, so the first screen needs aggregate counts plus a scan-friendly table
- relative report links should be computed from the catalog file location, not hard-coded absolute repo paths, so the artifact remains portable inside GitHub and local checkouts
- a blocked 2PC case is easier to compare when the landing page shows both the final outcome and whether any durable decision existed

## Self-test
1. Why add a separate `Decision` column when the table already has `Outcome`?
   - because blocked runs can have no visible decision even when the protocol story is not the same as a clean abort or commit; the distinction matters for crash analysis.
2. Why include per-scenario descriptions in the snapshots instead of forcing readers into the detailed report immediately?
   - because the catalog should stand alone as the fast recruiter-facing overview, with deep links as optional follow-up.
3. Why avoid indexing directly into `takeaways[-2]` for the snapshot summary?
   - because it couples the catalog renderer to the current takeaway ordering and makes future changes to the report copy unnecessarily fragile.

## Guardrails
- keep scenario ordering deterministic so committed catalog diffs stay stable
- regenerate per-scenario reports from the same command to avoid drift between the landing page and the detailed artifacts
- preserve the simple single-scenario `run` flow; the catalog is a companion bundle, not a replacement
