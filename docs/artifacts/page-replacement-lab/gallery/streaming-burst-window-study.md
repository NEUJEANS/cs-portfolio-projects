# Page Replacement Study Report

- workload: benchmark streaming-burst-window — stream-processing sliding window with cold backfill bursts and shifting hotsets
- frame range: 3 to 8
- reference length: 96
- best average faults: opt (37.50)

## Reference string

```text
10 11 12 13 10 11 12 13 14 15 10 11 12 13 10 11 12 13 14 15 10 11 12 13 10 11 12 13 14 15 50 51 52 53 54 55 56 57 12 13 14 15 12 13 16 17 12 13 14 15 12 13 16 17 12 13 14 15 12 13 16 17 70 71 72 73 74 75 76 77 78 79 14 15 16 17 14 15 18 19 14 15 16 17 14 15 18 19 14 15 16 17 14 15 18 19
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 3 | 96 | 96 | 96 | 59 | opt |
| 4 | 72 | 72 | 64 | 46 | opt |
| 5 | 72 | 71 | 64 | 36 | opt |
| 6 | 36 | 36 | 36 | 28 | opt |
| 7 | 36 | 36 | 36 | 28 | opt |
| 8 | 36 | 36 | 36 | 28 | opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
