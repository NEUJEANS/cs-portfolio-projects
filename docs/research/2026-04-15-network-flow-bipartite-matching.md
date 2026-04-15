# network-flow-lab bipartite matching slice research

## Goal
Add a meaningful follow-up slice to the existing max-flow lab without replacing the core Edmonds-Karp implementation.

## Notes
- Maximum bipartite matching is a standard reduction to max flow.
- Construction: add a super-source connected to each left-partition node with capacity 1, keep compatibility edges from left to right with capacity 1, and connect each right-partition node to a super-sink with capacity 1.
- The resulting max-flow value equals the matching size because each left and right node can participate in at most one unit of flow.
- Reusing the same solver gives a nice portfolio story: one general engine, multiple problem formulations.

## Slice choice
Implement a `match` / `match-demo` CLI path, sample input, tests, and README updates instead of adding visualization first. This keeps the run self-contained, algorithmically meaningful, and interview-friendly.
