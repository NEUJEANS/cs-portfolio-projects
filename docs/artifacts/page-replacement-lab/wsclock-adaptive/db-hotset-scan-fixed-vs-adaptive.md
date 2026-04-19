# WSClock Fixed vs Adaptive Comparison

- workload: benchmark db-hotset-scan — dashboard-style hot pages interrupted by analytics scans and checkpoint bursts
- frames: 5
- writeback penalty: 1.00
- dirty pages: none
- fixed sweep range: 1 to 10
- adaptive heuristic: recent reuse p50 over 10-reference segments
- adaptive window range: 3 to 10 (avg 4.40)
- best overall: tie between `tuned-fixed`, `adaptive-heuristic` (score 33.00)
- best fixed mode: `tuned-fixed`
- adaptive vs best fixed: **tied** (Δfaults +0, Δwritebacks +0, Δscore +0.00)

## Mode comparison

| Mode | Kind | Window | Faults | Hits | Hit rate | Writebacks | Weighted score |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| auto-fixed | fixed | auto (max(4, frames * 2)) | 34 | 50 | 59.52% | 0 | 34.00 |
| tuned-fixed | fixed | fixed 3 references | 33 | 51 | 60.71% | 0 | 33.00 |
| adaptive-heuristic | adaptive | adaptive segments of 10 references using recent reuse p50 | 33 | 51 | 60.71% | 0 | 33.00 |

## What changed vs the best fixed window

- auto-fixed minus tuned-fixed faults: 1
- adaptive minus tuned-fixed faults: 0
- adaptive minus auto-fixed faults: -1
- adaptive minus tuned-fixed writebacks: 0
- adaptive minus auto-fixed writebacks: 0

## Adaptive segment schedule

| Segment | References | τ window | History refs | History unique pages | Reuse percentile | Reuse p90 | Dirty ratio | Phase overlap | Reason |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 1 | 1..10 | 10 | 0 | 0 | — | — | 0.00 | — | initial auto window |
| 2 | 11..20 | 3 | 10 | 5 | 2.00 | 2.00 | 0.00 | 0.40 | recent reuse p50≈2.00, unique=5, phase_overlap=0.40 |
| 3 | 21..30 | 3 | 10 | 5 | 2.00 | 2.00 | 0.00 | 0.40 | recent reuse p50≈2.00, unique=5, phase_overlap=0.40 |
| 4 | 31..40 | 3 | 10 | 5 | 2.00 | 4.00 | 0.00 | 0.60 | recent reuse p50≈2.00, unique=5, phase_overlap=0.60 |
| 5 | 41..50 | 4 | 10 | 8 | 2.00 | 2.00 | 0.00 | 0.00 | recent reuse p50≈2.00, unique=8, phase_overlap=0.00 |
| 6 | 51..60 | 5 | 10 | 10 | — | — | 0.00 | 0.00 | recent history had no reuse, unique=10, phase_overlap=0.00 |
| 7 | 61..70 | 4 | 10 | 7 | 3.00 | 3.00 | 0.00 | 0.43 | recent reuse p50≈3.00, unique=7, phase_overlap=0.43 |
| 8 | 71..80 | 3 | 10 | 5 | 3.00 | 3.00 | 0.00 | 0.60 | recent reuse p50≈3.00, unique=5, phase_overlap=0.60 |
| 9 | 81..84 | 5 | 10 | 9 | 3.00 | 3.00 | 0.00 | 0.00 | recent reuse p50≈3.00, unique=9, phase_overlap=0.00 |

## Fixed-window sweep winner

The best fixed sweep window is τ=3 with score 33.00.