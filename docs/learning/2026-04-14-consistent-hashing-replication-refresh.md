# Consistent Hashing Replication Refresh — 2026-04-14

## Quick refresh
- `bisect_left` finds the first ring position at or after the key hash.
- Replica selection on a ring is naturally implemented by walking forward with wraparound.
- Distinct physical-node filtering matters because many adjacent ring points may belong to the same server due to virtual nodes.

## Self-test
1. Why can't replica selection just return the next `N` ring points?
   - Because multiple ring points can map to the same physical node; replicas must usually land on distinct physical nodes.
2. What is the maximum useful replication factor?
   - The number of distinct physical nodes in the ring.
3. What should remap comparison check for replicated placement?
   - Whether the replica set for each key changed, not only the primary owner.
