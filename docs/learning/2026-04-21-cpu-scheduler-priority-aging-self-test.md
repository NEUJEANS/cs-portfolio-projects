# 2026-04-21 cpu-scheduler priority aging refresh and self-test

## Refresher
- Use lower numeric priority as higher importance, which keeps comparisons easy to explain in README examples.
- Aging should only affect jobs that are waiting in the ready queue, not jobs that have not arrived yet.
- A simple deterministic policy is `effective_priority = base_priority - floor(wait_time / aging_interval)` when aging is enabled.
- For a non-preemptive priority scheduler, recompute effective priority only at dispatch boundaries.

## Self-test
1. If `P2(priority=5)` waits 6 ticks with `aging_interval=2`, what is its effective priority? `5 - floor(6/2) = 2`.
2. If `P3(priority=3)` arrives later and has only waited 2 ticks at the same dispatch boundary, what is its effective priority? `3 - floor(2/2) = 2`.
3. How should ties resolve? Earlier arrival first, then PID, so the ordering remains reproducible.

This matches the implementation plan for a deterministic portfolio-friendly priority scheduling slice.
