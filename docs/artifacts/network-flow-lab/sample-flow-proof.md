# Max-flow proof artifact: `sample_graph`

- Generated: 2026-04-17T07:45:28Z
- Algorithm: `dinic`
- Max flow: `19`
- Augmenting paths recorded: `4`
- Dinic phases: `2`

## Min-cut certificate

- Source side: c, s
- Sink side: a, b, d, t
- Cut capacity: `19`
- Max-flow/min-cut check: `True`

### Cut edges

- `c -> d` carries `9/9` (saturated=True)
- `s -> a` carries `10/10` (saturated=True)

## Augmenting paths

1. `s -> a -> b -> t` | bottleneck `4` (phase 1)
2. `s -> a -> d -> t` | bottleneck `6` (phase 1)
3. `s -> c -> d -> t` | bottleneck `4` (phase 1)
4. `s -> c -> d -> b -> t` | bottleneck `5` (phase 2)

## Narrative

- The final residual search reaches 2 node(s) on the source side and leaves 4 node(s) on the sink side.
- Edges that cross that partition have total capacity 19, which matches the computed max flow of 19.
- Every source-to-sink residual path is blocked once those cut edges are saturated, giving a concrete max-flow/min-cut certificate.
