# Page Replacement Imported Trace Comparison

- left trace: imported trace mobile-app-session — projects/page-replacement-lab/custom-traces/mobile-app-session.txt
- right trace: imported trace reporting-scan-session — projects/page-replacement-lab/custom-traces/reporting-scan-session.txt
- frame range: 3 to 8
- window size: 8
- phase threshold: 0.45
- WSClock window: auto (max(4, frames * 2))

## Trace overview

| Trace | References | Unique pages | Working-set avg | Phase hints | Best average faults |
| :--- | ---: | ---: | ---: | ---: | :--- |
| mobile-app-session | 60 | 30 | 6.15 | 6 | OPT (31.83) |
| reporting-scan-session | 24 | 18 | 6.54 | 2 | OPT (18.00) |

## Average algorithm comparison

| Algorithm | Left avg faults | Right avg faults | Δ right-left | Better avg | Left avg fault rate | Right avg fault rate |
| :--- | ---: | ---: | ---: | :--- | ---: | ---: |
| FIFO | 44.00 | 22.67 | -21.33 | right | 73.33% | 94.44% |
| CLOCK | 44.00 | 22.67 | -21.33 | right | 73.33% | 94.44% |
| AGING | 40.67 | 21.67 | -19.00 | right | 67.78% | 90.28% |
| WSCLOCK | 40.67 | 21.67 | -19.00 | right | 67.78% | 90.28% |
| LRU | 40.67 | 21.67 | -19.00 | right | 67.78% | 90.28% |
| OPT | 31.83 | 18.00 | -13.83 | right | 53.06% | 75.00% |

## Frame-by-frame comparison

| Frames | WSClock τ | Left winner | Right winner | FIFO L/R | CLOCK L/R | AGING L/R | WSCLOCK L/R | LRU L/R | OPT L/R |
| ---: | ---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | 6 | OPT | OPT | 53/24 | 53/24 | 51/24 | 51/24 | 51/24 | 37/18 |
| 4 | 8 | OPT | OPT | 50/24 | 50/24 | 48/24 | 48/24 | 48/24 | 33/18 |
| 5 | 10 | OPT | OPT | 44/24 | 44/24 | 38/24 | 38/24 | 38/24 | 31/18 |
| 6 | 12 | OPT | OPT | 41/22 | 41/22 | 37/20 | 37/20 | 37/20 | 30/18 |
| 7 | 14 | OPT | OPT | 41/22 | 41/22 | 35/20 | 35/20 | 35/20 | 30/18 |
| 8 | 16 | OPT | AGING/WSCLOCK/LRU/OPT | 35/20 | 35/20 | 35/18 | 35/18 | 35/18 | 30/18 |

## mobile-app-session locality snapshot

- working-set size: min 1, max 8, avg 6.15, final 6
- reuse distance: min 2, median 4.0, p90 11.0, max 15, avg 4.73
- hot pages: 4×8, 3×5, 5×5, 1×4, 2×4
- phase-boundary hints:
  - after reference 8: windows 1 -> 2 overlap 0.33; page-set overlap dropped sharply and the working set expanded.
  - after reference 16: windows 2 -> 3 overlap 0.17; page-set overlap dropped sharply and the working set contracted.
  - after reference 24: windows 3 -> 4 overlap 0.00; page-set overlap dropped sharply.
  - after reference 32: windows 4 -> 5 overlap 0.17; page-set overlap dropped sharply and the working set expanded.

## reporting-scan-session locality snapshot

- working-set size: min 1, max 8, avg 6.54, final 6
- reuse distance: min 5, median 5.0, p90 7.0, max 7, avg 5.67
- hot pages: 3×4, 4×4, 1×1, 2×1, 5×1
- phase-boundary hints:
  - after reference 8: windows 1 -> 2 overlap 0.14; page-set overlap dropped sharply.
  - after reference 16: windows 2 -> 3 overlap 0.17; page-set overlap dropped sharply and the working set contracted.

## mobile-app-session reference string

```text
1 2 3 1 2 4 1 2 3 5 1 2 8 9 10 11 12 8 9 13 14 15 8 9 3 4 5 3 4 16 17 18 19 20 3 4 21 22 23 24 25 21 22 26 27 28 21 22 4 5 6 4 5 29 30 31 4 5 6 4
```

## reporting-scan-session reference string

```text
1 2 3 4 5 6 7 8 9 10 3 4 11 12 13 14 3 4 15 16 17 18 3 4
```
