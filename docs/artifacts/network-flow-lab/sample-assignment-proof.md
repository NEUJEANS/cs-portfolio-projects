# Weighted assignment proof artifact: `sample_assignment_graph`

- Generated: `2026-04-17T13:45:27Z`
- Solver: `successive-shortest-path`
- Selected assignments: `3`
- Total cost: `12`
- Covers smaller partition: `True`

## Selected assignments

- `anna -> compiler` with cost `4`
- `ben -> api` with cost `2`
- `david -> database` with cost `6`

## Coverage summary

- Unmatched left: `chloe`
- Unmatched right: `(none)`
- Cost matches selected edges: `True`

## Min-cost-flow narrative

- The min-cost flow picked 3 assignment edge(s) with total cost 12.
- Each left node and right node is capped at one unit of flow, so any positive-cost path corresponds to a valid one-to-one assignment.
- Coverage of the smaller partition is complete, which makes it easy to see whether the input graph admitted a full assignment.

## Augmenting paths

- `source -> ben -> api -> sink` · bottleneck `1` · unit cost `2` · path cost `2`
- `source -> anna -> compiler -> sink` · bottleneck `1` · unit cost `4` · path cost `4`
- `source -> david -> database -> sink` · bottleneck `1` · unit cost `6` · path cost `6`
