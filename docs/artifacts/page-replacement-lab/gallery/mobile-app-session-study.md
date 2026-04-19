# Page Replacement Study Report

- workload: imported trace mobile-app-session — projects/page-replacement-lab/custom-traces/mobile-app-session.txt
- frame range: 3 to 8
- reference length: 60
- WSClock window: auto (max(4, frames * 2))
- best average faults: opt (31.83)

## Reference string

```text
1 2 3 1 2 4 1 2 3 5 1 2 8 9 10 11 12 8 9 13 14 15 8 9 3 4 5 3 4 16 17 18 19 20 3 4 21 22 23 24 25 21 22 26 27 28 21 22 4 5 6 4 5 29 30 31 4 5 6 4
```

## Key takeaways

- FIFO stays monotonic across this frame range.
- No non-FIFO regressions appear in this frame range.
- opt has the lowest average page-fault count across the full frame sweep.

## Faults by frame count

| Frames | FIFO | CLOCK | AGING | WSCLOCK | LRU | OPT | WSClock τ | Winner |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 3 | 53 | 53 | 51 | 51 | 51 | 37 | 6 | opt |
| 4 | 50 | 50 | 48 | 48 | 48 | 33 | 8 | opt |
| 5 | 44 | 44 | 38 | 38 | 38 | 31 | 10 | opt |
| 6 | 41 | 41 | 37 | 37 | 37 | 30 | 12 | opt |
| 7 | 41 | 41 | 35 | 35 | 35 | 30 | 14 | opt |
| 8 | 35 | 35 | 35 | 35 | 35 | 30 | 16 | opt |

## Regression callouts

- FIFO Belady anomalies: none in this study.

- Other fault regressions: none in this study.
