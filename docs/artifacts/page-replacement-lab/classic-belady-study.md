# Page Replacement Study Report

- workload: preset classic-belady — classic Belady anomaly reference string that makes FIFO regress from 3 to 4 frames
- frame range: 2 to 6
- reference length: 12
- best average faults: opt (6.40)

## Reference string

```text
1 2 3 4 1 2 5 1 2 3 4 5
```

## Key takeaways

- FIFO shows a Belady anomaly at frames 3 -> 4 (9 -> 10).
- clock also regresses at frames 3 -> 4 (9 -> 10).
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | Clock | LRU | OPT | Winner |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 2 | 12 | 12 | 12 | 9 | opt |
| 3 | 9 | 9 | 10 | 7 | opt |
| 4 | 10 | 10 | 8 | 6 | opt |
| 5 | 5 | 5 | 5 | 5 | fifo/clock/lru/opt |
| 6 | 5 | 5 | 5 | 5 | fifo/clock/lru/opt |

## Regression callouts

### FIFO Belady anomalies

- frames 3 -> 4: 9 -> 10 (+1)

### Other fault regressions

- clock: frames 3 -> 4 9 -> 10 (+1)
