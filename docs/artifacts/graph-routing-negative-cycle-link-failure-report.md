# routing_demo vs link_failure_demo route diff report

- Source: A
- Changed edges: 4
- Changed route entries: 3
- Unchanged route entries: 1
- Baseline negative cycle: none
- Candidate negative cycle: none

## Edge changes
| Source | Target | Baseline weight | Candidate weight | Change |
| --- | --- | --- | --- | --- |
| A | B | 4 | 2 | weight-changed |
| A | C | 2 | 4 | weight-changed |
| B | D | 2 | absent | removed |
| C | D | 5 | absent | removed |

## Route-table diff
| Node | Baseline cost | Baseline predecessor | Baseline path | Baseline status | Candidate cost | Candidate predecessor | Candidate path | Candidate status | Changed fields | Summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 1 | C | A -> C -> B | reachable | 2 | A | A -> B | reachable | cost, predecessor, path | cost 1 -> 2; predecessor C -> A; path: [A -> C -> B] => [A -> B] |
| C | 2 | A | A -> C | reachable | 4 | A | A -> C | reachable | cost | cost 2 -> 4 |
| D | 3 | B | A -> C -> B -> D | reachable | ∞ | — | unreachable | unreachable | status, cost, predecessor, path | status reachable -> unreachable; cost 3 -> ∞; predecessor B -> —; path: [A -> C -> B -> D] => [unreachable] |
