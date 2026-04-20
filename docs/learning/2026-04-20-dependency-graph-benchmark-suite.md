# Dependency graph planner benchmark-suite refresh — 2026-04-20

## Short refresh
- A benchmark suite is just structured orchestration around the existing planner: load graph, resolve capacities, replay strategies, then summarize results consistently.
- `best_makespan` and `rank_1` are not the same metric here: several strategies can tie on makespan while one still wins the queue-delay tie-break.
- Relative graph paths should resolve from the suite file location, not from the process working directory, or committed suites become fragile.
- Scenario-local resource overrides matter because the same DAG can change from a tie to a clear heuristic winner when one constrained resource is expanded.

## Self-test
1. What should the benchmark report teach that a single scenario report cannot?
   - It should show how strategy quality depends on workload shape and resource caps, not just one hand-picked example.
2. Why keep both `best_makespan_strategies` and `rank_1_strategies`?
   - Because equal makespans can still hide queue-delay differences, so the suite needs both the pure makespan winners and the deterministic tie-broken leaders.
3. What scenario proves inline resource-capacity overrides are worthwhile?
   - The multi-resource graph with `browser-lab=3`, where `fifo` improves to makespan `8` while the default-capacity version leaves all strategies tied at `10`.
