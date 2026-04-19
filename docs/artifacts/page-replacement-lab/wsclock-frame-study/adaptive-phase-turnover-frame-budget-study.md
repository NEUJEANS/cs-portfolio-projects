# WSClock Frame-Budget Study

- workload: benchmark adaptive-phase-turnover — three short overlapping hot-set phases crafted to show where an adaptive WSClock tau beats any single fixed window
- frame range: 2 to 6
- writeback penalty: 1.00
- dirty pages: none
- fixed sweep range: 1 to 9
- adaptive heuristic: recent reuse p50 with segment length 8
- adaptive vs best fixed: **better on 1 frame budgets**, tied on 4, worse on 0
- best average weighted score modes: `adaptive-heuristic`
- best average fault modes: `adaptive-heuristic`

## Average performance across the frame sweep

| Mode | Avg faults | Avg weighted score | Avg writebacks |
| :--- | ---: | ---: | ---: |
| auto-fixed | 10.60 | 10.60 | 0.00 |
| tuned-fixed | 10.60 | 10.60 | 0.00 |
| adaptive-heuristic | 10.40 | 10.40 | 0.00 |

## Per-frame outcomes

| Frames | Auto faults | Tuned faults | Adaptive faults | Tuned τ | Adaptive avg τ | Adaptive vs best fixed | Winner |
| ---: | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| 2 | 18 | 18 | 18 | 1 | 3.00 | tied (Δscore +0.00) | tuned-fixed |
| 3 | 14 | 14 | 13 | 1 | 3.67 | better (Δscore -1.00) | adaptive-heuristic |
| 4 | 8 | 8 | 8 | 1 | 4.33 | tied (Δscore +0.00) | tuned-fixed |
| 5 | 7 | 7 | 7 | 1 | 4.67 | tied (Δscore +0.00) | tuned-fixed |
| 6 | 6 | 6 | 6 | 1 | 4.67 | tied (Δscore +0.00) | tuned-fixed |

## Interpretation

- The strongest adaptive improvement appears at frame 3 with Δfaults -1, Δwritebacks +0, and Δscore -1.00 versus the best fixed mode.
- Adaptive never loses to the best fixed mode in this frame range.
- Adaptive wins on frame budgets: 3.
