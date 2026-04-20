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
| tarjan | 0.009546 |
| kosaraju | 0.014171 |

## Per-run timings (ms)
| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.013866 | 0.015570 | 0.001704 | tarjan |
| 2 | 0.008726 | 0.013085 | 0.004359 | tarjan |
| 3 | 0.007925 | 0.018756 | 0.010831 | tarjan |
| 4 | 0.009598 | 0.012103 | 0.002505 | tarjan |
| 5 | 0.007614 | 0.011341 | 0.003727 | tarjan |

## Component roster
- C0: A, B, C
- C1: D, E
- C2: F, G
- C3: H

## Interview talking points
- Both algorithms agree on the deterministic SCC grouping used by this lab.
- Tarjan averaged 0.009546 ms while Kosaraju averaged 0.014171 ms on this graph.
- The CSV export keeps one row per timing run so you can chart trial-by-trial variance in a spreadsheet or static portfolio page.
