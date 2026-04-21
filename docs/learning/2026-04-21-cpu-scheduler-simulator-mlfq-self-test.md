# CPU Scheduler Simulator Learning Note — 2026-04-21 MLFQ Self-Test

## Quick refresh
- MLFQ acts like a stack of round-robin queues: new work starts at the top, long-running work drifts downward, and periodic boosts pull runnable jobs back up so starvation does not linger forever.
- Smaller top-queue quanta improve response time, but with explicit context-switch accounting they can also make the dashboard look worse if the ladder is too aggressive.
- For this repo's CPU-only workloads, configurable queue ladders matter more than modeling blocking I/O, because the main portfolio goal is explainable cross-policy comparison.

## Self-test
1. **Q:** Why not hard-code one MLFQ ladder and hide it from the compare artifacts?  
   **A:** Because queue design is part of the policy. If the ladder is invisible, the benchmark screenshots are much less trustworthy or reproducible.

2. **Q:** Why keep a periodic boost in the default configuration?  
   **A:** Because the canonical teaching story includes anti-starvation boosts, and shipping boosts by default avoids presenting a starvation-prone variant as the project's main MLFQ example.

3. **Q:** Why prefer a `2,4,8` default ladder here instead of a smaller `1,2,4` ladder?  
   **A:** Because this project already tracks context-switch overhead explicitly, so the slightly wider ladder gives a cleaner portfolio tradeoff between quick response and avoidable dispatch churn.

## Pre-edit baseline check
- reran `python3 projects/cpu-scheduler-simulator/scheduler.py compare --preset interactive-bursts --quantum 2 --aging-interval 2 --context-switch-cost 1`
- confirmed the pre-MLFQ compare flow was healthy before editing, so any later regressions would be attributable to the new scheduler path instead of stale benchmark machinery
