# Distance Vector Routing Lab Review Log — 2026-04-15

## Review pass 1 — execution sanity
- Ran `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`.
- Ran CLI steady-state and failure simulations on small sample topologies.
- Found issue: the initial history snapshot was marked as `changed: true`, which makes the first round harder to explain in demos.
- Fix applied: initial round state now records `changed: false`, and coverage was expanded to assert that behavior.

## Review pass 2 — API and edge-case audit
- Checked whether the simulator output included enough context for saved artifacts and wrap-ups.
- Found issue: final JSON omitted the normalized topology, making exported results less self-contained.
- Fix applied: steady-state and failure simulations now include a normalized `topology` snapshot in the JSON payload, and tests were updated accordingly.
- Found issue: missing-edge removal behavior was not covered explicitly.
- Fix applied: added a regression test for rejecting nonexistent links.

## Review pass 3 — portfolio/docs integration audit
- Reviewed root README, master checklist, project README, and resumability docs for consistency.
- Found issue: the new project was not yet surfaced in the repo-level progress lists.
- Fix applied: added `distance-vector-routing-lab` to the root README and strengthened the master checklist with a dynamic-routing coverage item.
- Confirmed the slice is resumable with research, learning notes, checklist, implementation, tests, and review log in place.
