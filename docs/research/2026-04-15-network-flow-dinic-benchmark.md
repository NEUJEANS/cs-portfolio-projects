# Research — Network flow Dinic benchmark slice

## Why this slice
The project README already listed algorithm comparison as the next strongest follow-up after Graphviz export. Adding Dinic plus a benchmark deepens the portfolio story from “can solve max flow” to “can compare algorithmic trade-offs with reproducible evidence.”

## Notes from brief research
- Edmonds-Karp is the simpler educational baseline and has the well-known `O(V * E^2)` worst-case behavior.
- Dinic builds a level graph with BFS and pushes blocking flows, usually improving practical performance on larger or sparser graphs.
- For portfolio purposes, the most useful comparison is not giant theoretical claims but a small reproducible harness that verifies result parity and reports timing/augmentation counts.

## Implementation direction
- keep Edmonds-Karp as the default solver for continuity
- add `--algorithm {edmonds-karp,dinic}` to the existing flow and matching commands
- add a `benchmark` command that generates deterministic DAG-style flow graphs from a seed
- verify both algorithms return identical max-flow values on every generated trial before reporting timing statistics

## References
- https://cp-algorithms.com/graph/edmonds_karp.html
- https://www.topcoder.com/thrive/articles/edmonds-karp-and-dinics-algorithms-for-maximum-flow
- https://www.geeksforgeeks.org/dsa/dinics-algorithm-maximum-flow/
