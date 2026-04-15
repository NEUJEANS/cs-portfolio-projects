# Chord DHT refresh and self-test — 2026-04-15

## Refresh points
- In a Chord ring, a key belongs to the successor of the key's identifier.
- A node's `i`th finger starts at `(node_id + 2^i) mod 2^m`.
- Lookup can skip ahead with the closest preceding finger to reduce hop count.
- Adding a node should only move keys whose identifiers now fall into the new node's ownership interval.

## Self-test
1. If a node has ID 10 in a 5-bit ring, the first three finger starts are 11, 12, and 14.
2. If the key ID is 29 and the next clockwise node is 2, ownership wraps and that node is still responsible.
3. A joining node does not require every key to move; only the interval it newly covers should rebalance.

## Implementation reminders
- use modulo arithmetic consistently for wrap-around intervals
- keep traversal deterministic so tests and demos stay stable
- log lookup routes, not only final owners, so the project stays explainable
