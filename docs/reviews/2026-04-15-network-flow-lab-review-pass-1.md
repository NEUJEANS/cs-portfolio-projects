# network-flow-lab review pass 1

## Focus
Algorithm/design review of the new bipartite-matching slice.

## Findings
1. Good reuse of the existing Edmonds-Karp solver instead of forking a separate matching engine.
2. Risk found: bipartite input could reuse internal sentinel names like `__source__` / `__sink__`, which would collide with the reduction graph.

## Fixes applied
- added reserved-name validation in `load_bipartite_graph`
