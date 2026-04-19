# Page Replacement Trace Summary

- workload: imported trace mobile-app-session — projects/page-replacement-lab/custom-traces/mobile-app-session.txt
- reference length: 60
- unique pages: 30
- window size: 8
- first touches: 30
- reuses: 30
- working-set size (sliding window): min 1, max 8, avg 6.15, final 6
- reuse distance stats: min 2, median 4.0, p90 11.0, max 15, avg 4.73

## Top hot pages

| Page | Hits |
| ---: | ---: |
| 4 | 8 |
| 3 | 5 |
| 5 | 5 |
| 1 | 4 |
| 2 | 4 |

## Reuse distance buckets

| Bucket | Count |
| :--- | ---: |
| cold | 30 |
| 1-2 | 9 |
| 3-5 | 14 |
| 6-9 | 3 |
| 10+ | 4 |

## Window summaries

| Window | References | Unique pages | Hottest pages |
| ---: | :--- | ---: | :--- |
| 1 | 1..8 | 4 | 1×3, 2×3, 3×1 |
| 2 | 9..16 | 8 | 1×1, 2×1, 3×1 |
| 3 | 17..24 | 6 | 8×2, 9×2, 12×1 |
| 4 | 25..32 | 6 | 3×2, 4×2, 5×1 |
| 5 | 33..40 | 8 | 3×1, 4×1, 19×1 |
| 6 | 41..48 | 6 | 21×2, 22×2, 25×1 |
| 7 | 49..56 | 6 | 4×2, 5×2, 6×1 |
| 8 | 57..60 | 3 | 4×2, 5×1, 6×1 |

## Phase-boundary hints

- after reference 8: windows 1 -> 2 have Jaccard overlap 0.33; page-set overlap dropped sharply and the working set expanded.
- after reference 16: windows 2 -> 3 have Jaccard overlap 0.17; page-set overlap dropped sharply and the working set contracted.
- after reference 24: windows 3 -> 4 have Jaccard overlap 0.00; page-set overlap dropped sharply.
- after reference 32: windows 4 -> 5 have Jaccard overlap 0.17; page-set overlap dropped sharply and the working set expanded.
- after reference 40: windows 5 -> 6 have Jaccard overlap 0.17; page-set overlap dropped sharply and the working set contracted.
- after reference 48: windows 6 -> 7 have Jaccard overlap 0.00; page-set overlap dropped sharply.

## Reference string

```text
1 2 3 1 2 4 1 2 3 5 1 2 8 9 10 11 12 8 9 13 14 15 8 9 3 4 5 3 4 16 17 18 19 20 3 4 21 22 23 24 25 21 22 26 27 28 21 22 4 5 6 4 5 29 30 31 4 5 6 4
```
