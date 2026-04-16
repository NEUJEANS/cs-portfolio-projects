# Bipartite matching proof artifact: `sample_matching_graph`

- Generated: 2026-04-16T00:24:01Z
- Flow algorithm: `edmonds-karp`
- Match count: `3`
- Minimum vertex cover size: `3`
- König check: `True`

## Matches

- `anna -> api`
- `ben -> database`
- `chloe -> compiler`

## Minimum vertex cover

- Left cover vertices: (none)
- Right cover vertices: api, compiler, database
- Reachable unmatched-left expansion (left): anna, ben, chloe, david
- Reachable unmatched-left expansion (right): api, compiler, database

## Narrative

- The matching contains 3 edge(s), and the recovered minimum vertex cover contains 3 vertex/vertices.
- Unmatched left vertices seed alternating-path reachability; left vertices not reached and right vertices that are reached form the minimum cover.
- König's theorem check is satisfied, so the cover size matches the matching size.
