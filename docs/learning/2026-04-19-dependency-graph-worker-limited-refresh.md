# Dependency Graph Planner Refresh - 2026-04-19

## Short refresh
- Unlimited parallel layers describe dependency depth, but they do not model a real runner pool with only `k` workers.
- A worker-limited schedule can be simulated with an event loop: dispatch ready tasks, jump to the next completion time, release newly ready dependents, and repeat.
- Critical-path length and `ceil(total_work / workers)` form a useful lower bound for constrained makespan.
- Queue delay is `actual_start - ready_at`; it highlights tasks that waited only because workers were busy.

## Self-test
1. Why keep worker scheduling deterministic instead of just "any ready task"?
   - So reports, screenshots, tests, and interview explanations stay reproducible.
2. If a task has zero queue delay, what does that mean?
   - It started as soon as its dependencies were satisfied and a worker was available.
3. Why compare constrained makespan to the unlimited plan?
   - It makes the cost of the worker cap visible and explains whether slowdown came from true dependency bottlenecks or runnable work waiting in line.
