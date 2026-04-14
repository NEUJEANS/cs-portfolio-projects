# Consistent Hashing Refresh + Self-Test — 2026-04-14

## Refresh
- hash nodes and keys into the same address space
- assign each key to the first clockwise node on the ring
- use virtual nodes to smooth distribution
- when a node is added/removed, only nearby key ranges should move

## Self-test
1. Why use virtual nodes?
   - To reduce skew and improve load balancing.
2. What makes consistent hashing attractive?
   - It minimizes key remapping during topology changes.
3. What metric should the lab expose?
   - Key movement count/ratio plus distribution per node.
