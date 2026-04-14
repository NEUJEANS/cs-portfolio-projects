# Dependency Graph Planner Refresh - 2026-04-14

## Short refresh
- Kahn's algorithm gives a practical topological sort by repeatedly removing zero in-degree nodes.
- A deterministic planner should sort the ready queue so repeated runs produce the same order.
- Parallel layers can be derived from dependency depth once a valid topological order exists.
- Critical-path timing can be computed with a forward pass for earliest times and a backward pass for latest times.
- Slack is `latest_start - earliest_start`; zero-slack tasks are critical.

## Self-test
1. If two tasks become ready at the same time, why sort them?
   - To keep plans reproducible and test output stable.
2. What does a cycle in a build graph mean?
   - The dependency constraints are impossible to satisfy; no valid plan exists.
3. Why can a short project still have a long makespan?
   - Because the critical path dominates completion time even if many other tasks are parallelizable.
