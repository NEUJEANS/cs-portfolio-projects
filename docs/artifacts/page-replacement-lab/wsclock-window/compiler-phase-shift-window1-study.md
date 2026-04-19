# Page Replacement Study Report

- workload: benchmark compiler-phase-shift — larger compiler-style trace with parser hot loops, a code-generation scan, and optimizer table bursts
- frame range: 4 to 8
- reference length: 72
- WSClock window: fixed 1 reference
- best average faults: opt (33.40)

## Reference string

```text
1 2 3 4 1 2 5 6 1 2 3 4 1 2 5 6 1 2 3 4 1 2 5 6 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 7 8 9 10 7 8 11 12 7 8 9 10 7 8 11 12 7 8 9 10 7 8 11 12 40 41 7 8 9 10 40 41
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- wsclock also regresses at frames 4 -> 5 (52 -> 54).
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | CLOCK | AGING | WSCLOCK | LRU | OPT | WSClock τ | Winner |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 4 | 60 | 60 | 52 | 52 | 52 | 42 | 1 | opt |
| 5 | 60 | 58 | 52 | 54 | 52 | 35 | 1 | opt |
| 6 | 34 | 34 | 32 | 32 | 32 | 30 | 1 | opt |
| 7 | 34 | 34 | 32 | 34 | 32 | 30 | 1 | opt |
| 8 | 30 | 30 | 30 | 30 | 30 | 30 | 1 | fifo/clock/aging/wsclock/lru/opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

### Other fault regressions

- wsclock: frames 4 -> 5 52 -> 54 (+2)
- wsclock: frames 6 -> 7 32 -> 34 (+2)
