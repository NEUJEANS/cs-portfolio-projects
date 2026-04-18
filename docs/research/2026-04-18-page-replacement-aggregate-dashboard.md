# Research note — 2026-04-18 — page-replacement aggregate dashboard

## Question
What is the smallest meaningful next slice for `page-replacement-lab` after the per-workload gallery and trace-summary features?

## Decision
Skip extra web research for this slice.

## Why that was reasonable
- The missing capability was not a new algorithm; it was a **reporting layer** over the simulator and study outputs that already exist in the project.
- The key design choice is straightforward: compare workloads with a **shared frame range** and normalize by **reference length** so the built-in presets and larger benchmark traces can appear in one fair chart.
- That keeps the slice tight, implementation-focused, and easy to review within one cron run.

## Implementation choice
- Add an `aggregate` command instead of another replacement policy.
- Report per-workload average faults and normalized average page-fault rates across one frame sweep.
- Export CSV / SVG / JSON / HTML artifacts so the dashboard is useful both for slides and for future frontend/demo work.
- Leave working-set policies and richer trace-summary cards as future follow-up slices.
