# Dependency Graph Planner Research — 2026-04-20 — stress benchmark slice

## Goal
Extend the benchmark story with seeded stress workloads and clearer lower-bound reporting without derailing the already-in-progress dependency-graph planner slice.

## Research decision
No extra external web research was needed for this incremental follow-up.

## Why that was reasonable
- The project already had the core scheduling concepts implemented: critical path, constrained makespan, queue delay, renewable resources, and strategy comparisons.
- This slice reused the same benchmark/report/export pipeline rather than introducing a new algorithm family.
- The main design questions were repo-local product choices: how to shape deterministic stress DAGs, which benchmark metrics to surface, and how to present them in the existing Markdown/HTML/JSON/CSV bundle.

## Notes carried into implementation
- Keep the new workload synthetic but reproducible, so repeated exports stay deterministic and benchmark diffs remain reviewable.
- Make the stress generator produce a fragile critical chain plus competing bulk/fan-in work so strategy differences are visible under the same worker cap.
- Report both absolute gap and ratio versus the critical-path lower bound; the pair is easier to explain than raw makespan alone when scenarios vary in size.
- Refresh the committed benchmark artifacts after the code change so the portfolio story is visible directly from the repo browser.
