# Tarjan vs Kosaraju benchmark report

## Graph summary
| metric | value |
| --- | --- |
| graph file | `projects/tarjan-scc-lab/sample_graph.json` |
| node count | 8 |
| edge count | 10 |
| strongly connected components | 4 |
| repeated timing runs | 5 |
| algorithms match | yes |
| faster algorithm | tarjan |

## Average timings (ms)
| algorithm | average_ms |
| --- | ---: |
| tarjan | 0.008428 |
| kosaraju | 0.014586 |

## Per-run timings (ms)
| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.010470 | 0.017984 | 0.007514 | tarjan |
| 2 | 0.008927 | 0.012995 | 0.004068 | tarjan |
| 3 | 0.007624 | 0.016611 | 0.008987 | tarjan |
| 4 | 0.007785 | 0.011702 | 0.003917 | tarjan |
| 5 | 0.007334 | 0.013636 | 0.006302 | tarjan |

## Component roster
- C0: A, B, C
- C1: D, E
- C2: F, G
- C3: H

## Interview talking points
- Both algorithms agree on the deterministic SCC grouping used by this lab.
- Tarjan averaged 0.008428 ms while Kosaraju averaged 0.014586 ms on this graph.
- The CSV export keeps one row per timing run so you can chart trial-by-trial variance in a spreadsheet or static portfolio page.
