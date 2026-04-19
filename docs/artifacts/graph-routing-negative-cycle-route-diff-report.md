# routing_demo vs routing_shift_demo route diff report

- Source: A
- Changed edges: 2
- Changed route entries: 2
- Unchanged route entries: 2
- Baseline negative cycle: none
- Candidate negative cycle: none

## Edge changes
| Source | Target | Baseline weight | Candidate weight | Change |
| --- | --- | --- | --- | --- |
| C | B | -1 | 3 | weight-changed |
| C | D | 5 | 1 | weight-changed |

## Route-table diff
| Node | Baseline cost | Baseline predecessor | Baseline path | Baseline status | Candidate cost | Candidate predecessor | Candidate path | Candidate status | Changed fields | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 1 | C | A -> C -> B | reachable | 4 | A | A -> B | reachable | cost, predecessor, path | cost 1 -> 4; predecessor C -> A; path: [A -> C -> B] => [A -> B] |
| D | 3 | B | A -> C -> B -> D | reachable | 3 | C | A -> C -> D | reachable | predecessor, path | predecessor B -> C; path changed at same cost: [A -> C -> B -> D] => [A -> C -> D] |
