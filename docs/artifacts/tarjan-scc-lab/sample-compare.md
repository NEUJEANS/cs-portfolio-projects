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
| tarjan | 0.008829 |
| kosaraju | 0.013374 |

## Per-run timings (ms)
| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.010500 | 0.015450 | 0.004950 | tarjan |
| 2 | 0.011692 | 0.013155 | 0.001463 | tarjan |
| 3 | 0.007535 | 0.011442 | 0.003907 | tarjan |
| 4 | 0.006823 | 0.013606 | 0.006783 | tarjan |
| 5 | 0.007595 | 0.013215 | 0.005620 | tarjan |

## Component roster
- C0: A, B, C
- C1: D, E
- C2: F, G
- C3: H

## Interview talking points
- Both algorithms agree on the deterministic SCC grouping used by this lab.
- Tarjan averaged 0.008829 ms while Kosaraju averaged 0.013374 ms on this graph.
- The CSV export keeps one row per timing run so you can chart trial-by-trial variance in a spreadsheet or static portfolio page.
