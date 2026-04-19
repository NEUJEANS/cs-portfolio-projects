# WSClock Window Tuning Report

- workload: benchmark compiler-phase-shift — larger compiler-style trace with parser hot loops, a code-generation scan, and optimizer table bursts
- frames: 5
- candidate windows: 1 to 7
- writeback penalty: 1.00
- auto window: 10
- dirty pages: 1, 2, 3, 4, 5, 6
- recommended window: 7 (faults 52, writebacks 0, score 52.00)
- Pareto frontier windows: 7

## Why this recommendation

Window 7 minimizes the weighted score `faults + 1.00 × writebacks` for this workload and frame budget.
The built-in auto window `10` is outside this sweep, so it is listed for comparison only and was not evaluated directly.

## Candidate windows

| τ window | Faults | Hits | Hit rate | Writebacks | Weighted score |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 55 | 17 | 23.61% | 15 | 70.00 |
| 2 | 54 | 18 | 25.00% | 14 | 68.00 |
| 3 | 52 | 20 | 27.78% | 13 | 65.00 |
| 4 | 53 | 19 | 26.39% | 13 | 66.00 |
| 5 | 52 | 20 | 27.78% | 4 | 56.00 |
| 6 | 52 | 20 | 27.78% | 4 | 56.00 |
| 7 | 52 | 20 | 27.78% | 0 | 52.00 |

## Pareto frontier

These windows are not strictly dominated on both page faults and writebacks:

- τ=7: faults 52, writebacks 0, score 52.00