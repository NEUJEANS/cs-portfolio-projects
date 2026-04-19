# WSClock Frame-Budget Study

- workload: benchmark db-hotset-scan — dashboard-style hot pages interrupted by analytics scans and checkpoint bursts
- frame range: 3 to 8
- writeback penalty: 1.00
- dirty pages: none
- fixed sweep range: 2 to 14
- adaptive heuristic: recent reuse p50 with segment length 10
- adaptive vs best fixed: **better on 0 frame budgets**, tied on 5, worse on 1
- best average weighted score modes: `tuned-fixed`
- best average fault modes: `tuned-fixed`

## Average performance across the frame sweep

| Mode | Avg faults | Avg weighted score | Avg writebacks |
| :--- | ---: | ---: | ---: |
| auto-fixed | 40.50 | 40.50 | 0.00 |
| tuned-fixed | 39.17 | 39.17 | 0.00 |
| adaptive-heuristic | 39.67 | 39.67 | 0.00 |

## Per-frame outcomes

| Frames | Auto faults | Tuned faults | Adaptive faults | Tuned τ | Adaptive avg τ | Adaptive vs best fixed | Winner |
| ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| 3 | 62 | 62 | 62 | 2 | 3.48 | tied (Δscore +0.00) | tuned-fixed |
| 4 | 47 | 47 | 47 | 2 | 4.00 | tied (Δscore +0.00) | tuned-fixed |
| 5 | 34 | 33 | 33 | 3 | 4.40 | tied (Δscore +0.00) | tuned-fixed |
| 6 | 34 | 31 | 34 | 2 | 4.76 | worse (Δscore +3.00) | tuned-fixed |
| 7 | 34 | 31 | 31 | 2 | 5.12 | tied (Δscore +0.00) | tuned-fixed |
| 8 | 32 | 31 | 31 | 2 | 5.24 | tied (Δscore +0.00) | tuned-fixed |

## Interpretation

- Adaptive WSClock never beats the best fixed mode in this frame range, so this workload behaves like a tie-or-loss case rather than an adaptive win.
- Adaptive loses on frame budgets: 6.
- Adaptive does not outperform the best fixed mode on any frame budget in this study.
