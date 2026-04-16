# 2026-04-16 Consistent Hashing Virtual-Node Benchmark Refresh

## Refresher
- More virtual nodes usually reduce skew because each physical node samples more positions on the ring.
- Deterministic synthetic workloads are better than wall-clock-only benchmarks for small teaching labs because they make correctness and trend checks reproducible.
- Topology-change benchmarking should keep the key set fixed so movement ratios are attributable to the ring change, not to workload drift.

## Quick self-test
1. Why benchmark several virtual-node counts in one command? So the balance trend is visible without manually stitching together separate runs.
2. Why keep the output JSON-first? It is easy to test, inspect, and reuse for future chart/export slices.
3. Why include remap metrics in the same benchmark path? Because consistent hashing stories are about both steady-state balance and the cost of membership changes.
