# Splay Tree Refresh and Self-Test - 2026-04-15

## Refresh
- Splay on every successful search and on insert placement.
- On unsuccessful search, splay the last visited node so near-miss regions move closer to the root.
- Rotation cases:
  - zig: parent is root
  - zig-zig: node and parent are on the same side
  - zig-zag: node and parent are on opposite sides
- Delete by splaying the target to the root, separating left/right subtrees, then joining with the max node from the left side.

## Quick self-test
1. Why is a splay tree interesting even though a single operation can degrade to O(n)?
   - Because sequences of operations have amortized O(log n) cost and hot keys move closer to the root.
2. What should happen after a failed lookup?
   - Splay the last accessed node to improve locality around the search frontier.
3. How can two ordered splay trees be joined?
   - Splay the maximum node of the left tree, then attach the right tree as its right child.
