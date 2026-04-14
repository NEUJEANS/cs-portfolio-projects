# 2026-04-14 B-tree index refresh

## Quick refresh
- `bisect_left(keys, key)` gives the insertion/search slot while preserving sorted order.
- In a B-tree internal node, key `keys[i]` separates child `children[i]` (less than key) from `children[i+1]` (greater than key).
- For lower-bound style navigation, keep the best candidate seen so far when descending.
- For predecessor/successor queries, inspect the matching subtree when the exact key is present; otherwise keep the nearest ancestor candidate encountered while descending.

## Self-test
1. If a search key is missing but smaller than `keys[i]`, that key is a valid successor candidate.
2. If a search key is missing but larger than `keys[i]`, that key is a valid predecessor candidate.
3. When an exact key is present in an internal node, predecessor comes from the rightmost key in the left child and successor comes from the leftmost key in the right child.

## Planned slice
Add nearest-key navigation helpers (`floor`, `ceil`, and neighbors) plus CLI support and tests so the project better reflects real index-style workloads.
