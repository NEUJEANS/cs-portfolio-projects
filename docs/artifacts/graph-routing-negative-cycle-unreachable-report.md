# unreachable_demo routing report

- Nodes: 5
- Edges: 3

## Edge list
| Source | Target | Weight |
| --- | --- | --- |
| A | B | 3 |
| B | C | -1 |
| C | D | 2 |

## Bellman-Ford from A
| Node | Distance | Predecessor | Path | Status |
| --- | --- | --- | --- | --- |
| A | 0 | — | A | reachable |
| B | 3 | A | A -> B | reachable |
| C | 2 | B | A -> B -> C | reachable |
| D | 4 | C | A -> B -> C -> D | reachable |
| E | ∞ | — | unreachable | unreachable |

### Iteration log
- Iteration 1: changed; relaxed edges: A->B (3), B->C (-1), C->D (2)
- Iteration 2: stable; relaxed edges: none

## Johnson all-pairs shortest paths
| Source | Target | Cost | Path |
| --- | --- | --- | --- |
| A | A | 0 | A |
| A | B | 3 | A -> B |
| A | C | 2 | A -> B -> C |
| A | D | 4 | A -> B -> C -> D |
| A | E | ∞ | unreachable |
| B | A | ∞ | unreachable |
| B | B | 0 | B |
| B | C | -1 | B -> C |
| B | D | 1 | B -> C -> D |
| B | E | ∞ | unreachable |
| C | A | ∞ | unreachable |
| C | B | ∞ | unreachable |
| C | C | 0 | C |
| C | D | 2 | C -> D |
| C | E | ∞ | unreachable |
| D | A | ∞ | unreachable |
| D | B | ∞ | unreachable |
| D | C | ∞ | unreachable |
| D | D | 0 | D |
| D | E | ∞ | unreachable |
| E | A | ∞ | unreachable |
| E | B | ∞ | unreachable |
| E | C | ∞ | unreachable |
| E | D | ∞ | unreachable |
| E | E | 0 | E |
