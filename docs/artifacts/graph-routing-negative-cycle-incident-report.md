# routing_demo vs negative_cycle_demo route diff report

- Source: A
- Changed edges: 8
- Changed route entries: 4
- Unchanged route entries: 0
- Baseline negative cycle: none
- Candidate negative cycle: A -> B -> C -> A

## Edge changes
| Source | Target | Baseline weight | Candidate weight | Change |
| --- | --- | --- | --- | --- |
| A | B | 4 | 3 | weight-changed |
| A | C | 2 | absent | removed |
| B | C | absent | 2 | added |
| B | D | 2 | absent | removed |
| C | A | absent | -8 | added |
| C | B | -1 | absent | removed |
| C | D | 5 | 4 | weight-changed |
| D | A | 1 | absent | removed |

## Route-table diff
| Node | Baseline cost | Baseline predecessor | Baseline path | Baseline status | Candidate cost | Candidate predecessor | Candidate path | Candidate status | Changed fields | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 | — | A | reachable | -9 | C | A | cycle-reachable | status, cost, predecessor | status reachable -> cycle-reachable; cost 0 -> -9; predecessor — -> C |
| B | 1 | C | A -> C -> B | reachable | -3 | A | unreachable | cycle-reachable | status, cost, predecessor, path | status reachable -> cycle-reachable; cost 1 -> -3; predecessor C -> A; path: [A -> C -> B] => [unreachable] |
| C | 2 | A | A -> C | reachable | -1 | B | A -> B -> C | cycle-reachable | status, cost, predecessor, path | status reachable -> cycle-reachable; cost 2 -> -1; predecessor A -> B; path: [A -> C] => [A -> B -> C] |
| D | 3 | B | A -> C -> B -> D | reachable | 3 | C | A -> B -> C -> D | cycle-reachable | status, predecessor, path | status reachable -> cycle-reachable; predecessor B -> C; path changed at same cost: [A -> C -> B -> D] => [A -> B -> C -> D] |
