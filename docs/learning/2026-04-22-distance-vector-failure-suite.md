# Distance Vector Failure Suite Refresh

- Date: 2026-04-22
- Project: `distance-vector-routing-lab`

## Quick refresh
- a good benchmark suite should mix isolated-destination cases and alternate-path cases, otherwise every comparison tells the same story
- suite output should keep per-scenario detail, but also roll up a scorecard so recruiters can scan it quickly
- `max_rounds` belongs in the exported suite metadata because non-convergence within the budget is itself a useful routing story

## Self-test
Q: Why include a ring-isolation scenario when the tiny `A-B-C` example already shows count to infinity?
A: Because the line mostly demonstrates the classic two-router deception case. A larger ring shows that split horizon and poison reverse improve behavior without magically eliminating every longer loop immediately.
