# Fenwick vs segment tree refresh

## Quick notes
- Fenwick trees are excellent when the operation can be expressed with invertible prefix sums.
- The dual-tree trick supports range add plus range sum while keeping O(log n) updates and queries.
- A lazy segment tree handles the same range add plus range sum workload with O(log n) updates and queries too, but with a larger constant factor and more implementation complexity.
- Comparing both on the exact same deterministic workload creates a better portfolio story than quoting asymptotic complexity alone.

## Self-test
1. Why are two Fenwick trees enough for range add plus range sum?
   - Because the range update can be encoded as prefix-delta adjustments, and the final prefix sum is reconstructed from two weighted prefix accumulators.
2. Why benchmark against a lazy segment tree instead of a naive array?
   - Because the segment tree has the same asymptotic guarantees on the same workload, so the comparison is more meaningful for interview tradeoffs.
3. What must be verified before trusting timing comparisons?
   - Both structures must produce the same query checksum and the same final total after replaying the identical operation stream.
