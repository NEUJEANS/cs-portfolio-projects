# Page Replacement Study Report

- workload: preset looping-hotset — small hot working set with a short burst page that rewards recency-aware policies
- frame range: 3 to 8
- reference length: 12
- best average faults: opt (4.33)

## Reference string

```text
1 2 3 1 2 4 1 2 3 4 1 2
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | CLOCK | AGING | WSCLOCK | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 3 | 10 | 10 | 8 | 8 | 8 | 6 | opt |
| 4 | 4 | 4 | 4 | 4 | 4 | 4 | fifo/clock/aging/wsclock/lru/opt |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | fifo/clock/aging/wsclock/lru/opt |
| 6 | 4 | 4 | 4 | 4 | 4 | 4 | fifo/clock/aging/wsclock/lru/opt |
| 7 | 4 | 4 | 4 | 4 | 4 | 4 | fifo/clock/aging/wsclock/lru/opt |
| 8 | 4 | 4 | 4 | 4 | 4 | 4 | fifo/clock/aging/wsclock/lru/opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
