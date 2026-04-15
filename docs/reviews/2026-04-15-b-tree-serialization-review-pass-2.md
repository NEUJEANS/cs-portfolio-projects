# 2026-04-15 B-tree serialization review pass 2

## Focus
Structural validation review for deserialized trees.

## Issue found
- The first validation pass checked capacities and global item ordering, but it did not verify that each child subtree stayed inside the separator-key bounds imposed by its parent.
- A malformed snapshot could place a key like `8` in the right child of parent key `10` and still pass the older checks.

## Fix
- Extended `_validate_node(...)` to carry `lower_bound` / `upper_bound` constraints recursively and reject keys outside the allowed subtree range.

## Result
- Deserialization now rejects a broader class of corrupted or hand-edited snapshots while preserving valid trees.
