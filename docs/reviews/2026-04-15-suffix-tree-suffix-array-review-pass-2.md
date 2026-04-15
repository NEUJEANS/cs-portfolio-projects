# Review pass 2 — suffix-tree suffix-array benchmark slice

## Focus
Code audit for the naive suffix-array search path.

## Findings
- confirmed the suffix array is built once per `SuffixTree` instance and reused across benchmark iterations, keeping timings focused on lookup cost
- checked that empty patterns are still rejected at the suffix-array boundary
- verified the search loop exits once it leaves the contiguous matching suffix window, avoiding unnecessary scans across the rest of the array

## Result
- no further code changes required in this pass
