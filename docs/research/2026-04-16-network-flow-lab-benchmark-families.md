# 2026-04-16 network-flow-lab benchmark family research

## Why this slice
The benchmark mode already compared Edmonds-Karp and Dinic on random DAGs, but that left out graph families where residual rerouting and cut-heavy phase structure are easier to see. A stronger portfolio slice is to benchmark multiple graph shapes with different algorithm stories.

## Brief research notes
- cp-algorithms' Edmonds-Karp reference emphasizes the classic `O(V * E^2)` worst-case behavior, which gets more painful as graphs become dense.
- Quick follow-up search notes on Dinic consistently highlight that layered/blocking-flow structure tends to pay off more clearly on denser or more structured flow networks than on tiny sparse DAGs.
- That suggests the benchmark should include at least one denser residual-style family and one layered family, not just random DAGs.

## Chosen implementation direction
- keep the existing DAG generator as the baseline
- add a `dense` family with extra source/sink shortcuts plus guaranteed backward middle-node edges to create more residual rerouting
- add a `layered` family with dense adjacent layers and optional skip edges to make cut-heavy phases easier to compare
- expose the family choice in the CLI so README examples and future artifacts can point to repeatable commands

## Sources
- https://cp-algorithms.com/graph/edmonds_karp.html
- https://web.stanford.edu/class/archive/cs/cs161/cs161.1168/lecture16.pdf
