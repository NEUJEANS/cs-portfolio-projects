# KD-Tree k-Nearest Refresh — 2026-04-15

## Quick refresh
- maintain a bounded max-heap of the current best `k` candidates so the root holds the current worst accepted neighbor
- always traverse the branch containing the query point first, then prune the opposite branch only when the splitting-plane distance exceeds the current worst accepted distance
- for deterministic outputs, sort equal-distance candidates with a stable secondary key such as `(x, y, label)`

## Self-test
- if `k=1`, the algorithm should reduce to standard nearest-neighbor search
- if `k` exceeds dataset size, return all points in ranked order rather than failing
- benchmark validation should assert KD-tree and brute-force outputs match before reporting timing numbers
