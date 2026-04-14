# external-merge-sort-lab research - 2026-04-14

## Brief findings
- external merge sort is the standard approach when the full dataset cannot fit in RAM
- the workflow is split into run generation and one or more k-way merge passes
- larger chunk sizes reduce the number of initial runs, while larger merge fan-in reduces merge rounds at the cost of more open run streams and heap work per step

## Slice decision
Build a compact Python CLI that sorts integer files, surfaces run/merge statistics, and stays easy to understand in a student portfolio.
