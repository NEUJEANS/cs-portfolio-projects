# Red-black tree order-statistics refresh

## Refresher
- Red-black balancing rules stay unchanged when adding subtree sizes; the augmentation is orthogonal to color repair.
- The safe maintenance pattern is:
  1. increment ancestors on the insert descent path
  2. refresh nodes touched by each rotation
  3. refresh upward once fix-up completes

## Quick self-test
- If `rank(17)` is queried on inorder keys `[5, 10, 15, 20, 25, 30, 35]`, the answer should be `3`.
- If `select(4)` is queried on the same tree, the answer should be `25`.
- A valid root subtree size should always equal tree size.
