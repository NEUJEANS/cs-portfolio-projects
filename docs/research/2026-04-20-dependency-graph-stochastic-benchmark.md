# Dependency Graph Planner Research — 2026-04-20 — stochastic benchmark slice

## Goal
Extend the dependency-graph planner benchmark story from deterministic seeded stress workloads into uncertainty-aware scheduler comparisons without introducing a heavyweight simulator.

## Research decision
No extra external web research was required for this incremental follow-up.

## Why that was reasonable
- The repo already had the benchmark-suite pipeline, seeded stress workloads, critical-path lower-bound reporting, and the core ready-queue heuristics in place.
- This slice was mainly a modeling and presentation decision: how to resample task durations in a deterministic, reviewable way and surface the results in the existing Markdown/HTML/JSON/CSV bundle.
- The project goal is a strong student portfolio artifact, so a lightweight, explainable uncertainty model was more valuable than a much larger simulation framework.

## Notes carried into implementation
- Use a seeded triangular range per task so each replay keeps the original manifest duration as the mode while still allowing optimistic/pessimistic variation.
- Keep the stochastic scenarios focused on the seeded stress workloads, where heuristic differences are already visible and easy to explain.
- Report average, p50, p90, worst-case, and best-finish-rate metrics so the portfolio story covers both central tendency and tail behavior.
- Refresh the committed benchmark artifacts after the code change so the uncertainty story is visible directly from the repo browser.
