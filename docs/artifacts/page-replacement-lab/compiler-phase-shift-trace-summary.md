# Page Replacement Trace Summary

- workload: benchmark compiler-phase-shift — larger compiler-style trace with parser hot loops, a code-generation scan, and optimizer table bursts
- reference length: 72
- unique pages: 30
- window size: 12
- first touches: 30
- reuses: 42
- working-set size (sliding window): min 1, max 12, avg 7.72, final 8
- reuse distance stats: min 3, median 5.0, p90 5.0, max 7, avg 4.14

## Top hot pages

| Page | Hits |
| ---: | ---: |
| 7 | 7 |
| 8 | 7 |
| 1 | 6 |
| 2 | 6 |
| 9 | 4 |

## Reuse distance buckets

| Bucket | Count |
| :--- | ---: |
| cold | 30 |
| 1-2 | 0 |
| 3-5 | 40 |
| 6-9 | 2 |
| 10+ | 0 |

## Window summaries

| Window | References | Unique pages | Hottest pages |
| ---: | :--- | ---: | :--- |
| 1 | 1..12 | 6 | 1×3, 2×3, 3×2 |
| 2 | 13..24 | 6 | 1×3, 2×3, 5×2 |
| 3 | 25..36 | 12 | 20×1, 21×1, 22×1 |
| 4 | 37..48 | 10 | 7×2, 8×2, 9×1 |
| 5 | 49..60 | 6 | 7×3, 8×3, 9×2 |
| 6 | 61..72 | 8 | 7×2, 8×2, 40×2 |

## Phase-boundary hints

- after reference 24: windows 2 -> 3 have Jaccard overlap 0.00; page-set overlap dropped sharply and the working set expanded.
- after reference 36: windows 3 -> 4 have Jaccard overlap 0.00; page-set overlap dropped sharply.

## Reference string

```text
1 2 3 4 1 2 5 6 1 2 3 4 1 2 5 6 1 2 3 4 1 2 5 6 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 7 8 9 10 7 8 11 12 7 8 9 10 7 8 11 12 7 8 9 10 7 8 11 12 40 41 7 8 9 10 40 41
```
