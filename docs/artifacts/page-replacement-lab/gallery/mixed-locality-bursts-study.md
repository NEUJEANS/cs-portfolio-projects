# Page Replacement Study Report

- workload: preset mixed-locality-bursts — alternates hot-loop bursts with cold misses to mimic uneven interactive workloads
- frame range: 2 to 6
- reference length: 18
- best average faults: opt (7.80)

## Reference string

```text
1 2 1 2 3 4 1 2 5 1 2 6 1 2 3 4 1 2
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 2 | 16 | 16 | 16 | 12 | opt |
| 3 | 14 | 14 | 12 | 8 | opt |
| 4 | 12 | 12 | 8 | 7 | opt |
| 5 | 10 | 10 | 8 | 6 | opt |
| 6 | 6 | 6 | 6 | 6 | fifo/clock/lru/opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
