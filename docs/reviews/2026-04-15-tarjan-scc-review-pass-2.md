# 2026-04-15 tarjan-scc review pass 2

## Focus
Output quality for demos and downstream tooling.

## Improvements made
- enriched SCC summary with `cyclic_component_count`, `source_component_count`, `sink_component_count`, and `condensation_edge_count`
- enriched condensation output with component sizes and total DAG edge count
- kept output deterministic for tests and interview demos
