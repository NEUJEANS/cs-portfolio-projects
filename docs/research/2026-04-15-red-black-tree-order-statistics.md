# Red-black tree order-statistics slice research

## Goal
Augment the existing red-black tree lab with order-statistics operations that are useful in interviews and systems discussions.

## Notes
- CLRS-style order-statistics trees augment each node with subtree size metadata.
- `rank(x)` can be answered by walking from the root and summing left-subtree sizes whenever traversal goes right.
- `select(k)` can be answered by comparing `k` with the current node's left-subtree size.
- Rotations must refresh subtree sizes for the pivot and promoted child, otherwise metadata silently drifts.
- Validation should check subtree-size consistency so augmentation bugs are caught quickly.

## Planned slice
- add `subtree_size` to each node
- maintain metadata through insertion path updates and rotations
- expose `rank` and `select` APIs plus CLI commands
- extend tests to cover metadata validation and CLI behavior
