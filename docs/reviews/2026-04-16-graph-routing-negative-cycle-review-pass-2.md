# graph-routing-negative-cycle-lab review — pass 2 (smoke checks)

- Ran Bellman-Ford smoke test on `negative_cycle_graph.json` and confirmed the CLI reports `A -> B -> C -> A` as a reachable negative cycle.
- Ran Johnson pretty-mode smoke test on `sample_graph.json` and confirmed the all-pairs routing table includes the `A -> C -> B -> D` shortest path with total cost `3`.
- Re-ran the repository test suite after the pretty-output tweak; all tests stayed green.
