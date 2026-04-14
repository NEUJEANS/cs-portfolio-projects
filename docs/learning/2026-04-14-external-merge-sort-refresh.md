# external-merge-sort-lab refresh - 2026-04-14

## Refresher
- `heapq` is the clean standard-library tool for k-way merge selection
- temporary run files fit naturally with `tempfile.TemporaryDirectory`
- a good self-test is to predict run counts and merge rounds from `(n, chunk_size, fan_in)` before coding

## Self-test
- 9 numbers with chunk size 2 produce 5 runs
- merging 5 runs with fan-in 2 takes 3 rounds: `5 -> 3 -> 2 -> 1`
- duplicates and negative numbers should survive unchanged in sorted order
