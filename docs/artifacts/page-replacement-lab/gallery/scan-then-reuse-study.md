# Page Replacement Study Report

- workload: preset scan-then-reuse — large sequential scan followed by a tighter reuse window to show cache pollution pressure
- frame range: 2 to 6
- reference length: 15
- best average faults: opt (8.40)

## Reference string

```text
1 2 3 4 5 6 1 2 3 1 2 7 1 2 3
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 2 | 15 | 15 | 15 | 12 | opt |
| 3 | 13 | 13 | 11 | 9 | opt |
| 4 | 10 | 10 | 10 | 7 | opt |
| 5 | 10 | 10 | 10 | 7 | opt |
| 6 | 10 | 10 | 7 | 7 | lru/opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
