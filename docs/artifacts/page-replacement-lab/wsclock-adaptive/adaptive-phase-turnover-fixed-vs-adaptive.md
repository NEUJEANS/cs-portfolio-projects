# WSClock Fixed vs Adaptive Comparison

- workload: benchmark adaptive-phase-turnover — three short overlapping hot-set phases crafted to show where an adaptive WSClock tau beats any single fixed window
- frames: 3
- writeback penalty: 1.00
- dirty pages: none
- fixed sweep range: 1 to 9
- adaptive heuristic: recent reuse p50 over 8-reference segments
- adaptive window range: 2 to 6 (avg 3.67)
- best overall: `adaptive-heuristic` (faults 13, writebacks 0, score 13.00)
- best fixed mode: `tuned-fixed`
- adaptive vs best fixed: **better** (Δfaults -1, Δwritebacks +0, Δscore -1.00)

## Mode comparison

| Mode | Kind | Window | Faults | Hits | Hit rate | Writebacks | Weighted score |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| auto-fixed | fixed | auto (max(4, frames * 2)) | 14 | 10 | 41.67% | 0 | 14.00 |
| tuned-fixed | fixed | fixed 1 references | 14 | 10 | 41.67% | 0 | 14.00 |
| adaptive-heuristic | adaptive | adaptive segments of 8 references using recent reuse p50 | 13 | 11 | 45.83% | 0 | 13.00 |

## What changed vs the best fixed window

- auto-fixed minus tuned-fixed faults: 0
- adaptive minus tuned-fixed faults: -1
- adaptive minus auto-fixed faults: -1
- adaptive minus tuned-fixed writebacks: 0
- adaptive minus auto-fixed writebacks: 0

## Adaptive segment schedule

| Segment | References | τ window | History refs | History unique pages | Reuse percentile | Reuse p90 | Dirty ratio | Phase overlap | Reason |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 1 | 1..8 | 6 | 0 | 0 | — | — | 0.00 | — | initial auto window |
| 2 | 9..16 | 3 | 8 | 5 | 2.00 | 3.00 | 0.00 | 0.40 | recent reuse p50≈2.00, unique=5, phase_overlap=0.40 |
| 3 | 17..24 | 2 | 8 | 4 | 2.00 | 3.00 | 0.00 | 1.00 | recent reuse p50≈2.00, unique=4, phase_overlap=1.00 |

## Fixed-window sweep winner

The best fixed sweep window is τ=1 with score 14.00.