# Learning refresh — 2026-04-15 red-black-tree deletion slice

## Quick refresh
- If the deleted node has two children, move work to its inorder successor because that successor has no left child.
- Deleting a red node is easy; deleting a black node can reduce black height on one path and triggers fix-up.
- The core delete-fixup cases are: red sibling rotation, black sibling with two black children (push deficit upward), and black sibling with an outer/inner red child (rotate + recolor to absorb the deficit).
- Subtree-size augmentation needs updates after transplants and rotations, not just insertion paths.

## Self-test
1. Why use the inorder successor for two-child deletion?
   - Because it preserves BST ordering and reduces the actual removed node to a zero/one-child case.
2. What makes delete-fixup harder than insert-fixup?
   - The missing black height can propagate upward through multiple levels, especially when the replacement child is black or `None`.
3. What extra bookkeeping matters for order-statistics support?
   - Refresh `subtree_size` on ancestors affected by transplants and on the nodes touched by rotations.
