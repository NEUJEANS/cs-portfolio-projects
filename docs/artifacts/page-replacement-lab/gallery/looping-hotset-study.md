# Page Replacement Study Report

- workload: preset looping-hotset — small hot working set with a short burst page that rewards recency-aware policies
- frame range: 2 to 6
- reference length: 12
- best average faults: opt (5.40)

## Reference string

```text
1 2 3 1 2 4 1 2 3 4 1 2
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 2 | 12 | 12 | 12 | 9 | opt |
| 3 | 10 | 10 | 8 | 6 | opt |
| 4 | 4 | 4 | 4 | 4 | fifo/clock/lru/opt |
| 5 | 4 | 4 | 4 | 4 | fifo/clock/lru/opt |
| 6 | 4 | 4 | 4 | 4 | fifo/clock/lru/opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
