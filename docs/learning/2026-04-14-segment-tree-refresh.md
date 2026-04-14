# 2026-04-14 segment tree refresh

## Refresher
- segment trees answer interval queries by recursively partitioning the array into power-of-two-like segments
- each query touches only the nodes whose segments intersect the requested interval, giving `O(log n)` node visits on balanced paths
- lazy propagation defers pushing a range update into children until a later query or update actually needs that subtree
- for range-add updates, sum changes by `delta * segment_length`, while min and max each shift by `delta`

## Self-test
1. Why not use prefix sums here?
   - Prefix sums handle range sums well but do not support efficient point-set plus min/max plus bulk range-add updates together.
2. Why can min/max be updated lazily for range-add?
   - Adding the same delta to every element in a covered segment shifts both min and max by the same delta.
3. What is the key invariant after `_push`?
   - Any pending delta stored at a parent has been transferred into its children, so child aggregates are safe to read or refine.
