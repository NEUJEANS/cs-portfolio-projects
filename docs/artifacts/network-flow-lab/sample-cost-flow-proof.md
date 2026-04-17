# Min-cost flow proof artifact: `sample_cost_flow_graph`

- Generated: `2026-04-17T12:11:43Z`
- Solver: `successive-shortest-path`
- Requested flow: `2`
- Delivered flow: `2`
- Total cost: `5`
- Average cost per unit: `2.5`

## Edges carrying flow

- `a -> c` carries `1/1` at unit cost `2`
- `b -> c` carries `1/1` at unit cost `1`
- `c -> t` carries `2/2` at unit cost `1`
- `s -> a` carries `1/2` at unit cost `0`
- `s -> b` carries `1/1` at unit cost `0`

## Coverage summary

- Target reached: `True`
- Cost matches used edges: `True`

## Residual-path narrative

- The solver shipped 2 unit(s) of flow out of the requested 2 with total cost 5.
- Every positive-flow edge contributes `flow × cost` to the certificate, so the selected residual paths can be audited directly from the exported edge table.
- The requested flow target was reached before the residual graph ran out of augmenting paths.

## Augmenting paths

- `s -> b -> c -> t` · bottleneck `1` · unit cost `2` · path cost `2`
- `s -> a -> c -> t` · bottleneck `1` · unit cost `3` · path cost `3`
