# Tarjan vs Kosaraju benchmark report

## Graph summary
| metric | value |
| --- | --- |
| graph file | `sample_graph.json` |
| node count | 8 |
| edge count | 10 |
| strongly connected components | 4 |
| repeated timing runs | 5 |
| algorithms match | yes |
| faster algorithm | tarjan |

## Average timings (ms)
| algorithm | average_ms |
| --- | ---: |
| tarjan | 0.008588 |
| kosaraju | 0.013147 |

## Per-run timings (ms)
| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.010481 | 0.018749 | 0.008268 | tarjan |
| 2 | 0.009019 | 0.013277 | 0.004258 | tarjan |
| 3 | 0.007465 | 0.011484 | 0.004019 | tarjan |
| 4 | 0.006784 | 0.011143 | 0.004359 | tarjan |
| 5 | 0.009189 | 0.011083 | 0.001894 | tarjan |

## Component roster
- C0: A, B, C
- C1: D, E
- C2: F, G
- C3: H

## Interview talking points
- Both algorithms agree on the deterministic SCC grouping used by this lab.
- Tarjan averaged 0.008588 ms while Kosaraju averaged 0.013147 ms on this graph.
- The CSV export keeps one row per timing run so you can chart trial-by-trial variance in a spreadsheet or static portfolio page.
