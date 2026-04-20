# Dependency Graph Planner Refresh — 2026-04-20 — stochastic benchmark slice

## Quick refresh
- Triangular-duration replays fit this project well because they keep the authored manifest duration as the most likely case while still modeling optimistic and pessimistic outcomes.
- The benchmark bundle already had deterministic makespan, lower-bound gap, and ratio reporting, so the uncertainty extension should reuse the same scenario/strategy structure rather than inventing a separate reporting path.
- For a recruiter-facing artifact, p50/p90/worst-case summaries are easier to explain than raw per-sample traces.

## Self-test before editing
- Deterministic expectation: if the stochastic seed/config are fixed, rerunning the same benchmark suite should produce byte-identical JSON output.
- Product expectation: the suite/report should still be useful even when only some scenarios opt into `stochastic_durations`.
- UX expectation: README and checklist docs must describe the new scenario field so the feature is discoverable from the repo browser.
