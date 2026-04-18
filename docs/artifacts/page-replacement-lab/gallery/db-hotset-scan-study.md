# Page Replacement Study Report

- workload: benchmark db-hotset-scan — dashboard-style hot pages interrupted by analytics scans and checkpoint bursts
- frame range: 3 to 8
- reference length: 84
- best average faults: opt (32.33)

## Reference string

```text
1 2 3 1 2 4 1 2 5 1 2 3 1 2 4 1 2 5 1 2 3 1 2 4 1 2 5 1 2 3 1 2 4 1 2 5 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 1 2 3 6 1 2 3 7 1 2 3 6 1 2 3 7 1 2 3 6 1 2 3 7 60 61 62 63 1 2 3 4
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 3 | 72 | 72 | 62 | 48 | opt |
| 4 | 59 | 54 | 47 | 37 | opt |
| 5 | 34 | 34 | 34 | 28 | opt |
| 6 | 34 | 34 | 34 | 27 | opt |
| 7 | 34 | 34 | 34 | 27 | opt |
| 8 | 34 | 34 | 31 | 27 | opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
