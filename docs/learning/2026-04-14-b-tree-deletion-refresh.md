# 2026-04-14 B-tree deletion refresh

## Quick refresh
- Minimum degree `t` means every non-root node should keep between `t-1` and `2t-1` keys.
- Deletion cases to handle:
  1. delete directly from a leaf when the key is present
  2. delete from an internal node by swapping with predecessor/successor when a neighboring child has spare capacity
  3. merge two minimal children around a separator key when neither side can lend
  4. before descending, rebalance so the next child has at least `t` keys
  5. shrink the root if it becomes empty and has a single child

## Self-test checklist
- Can I explain why deletion rebalances *before* descending? Yes: it avoids recursing into an underfull child and simplifies invariants.
- Can I explain predecessor vs successor replacement? Yes: replace the internal key with an adjacent in-order key from a subtree that can safely spare one.
- Can I explain root shrinking? Yes: once the root loses its last key, its sole child becomes the new root to reduce tree height.
