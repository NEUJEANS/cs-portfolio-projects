# AVL tree refresh - 2026-04-15

## Quick refresh
- AVL trees maintain BST ordering plus a height-balance invariant: for every node, `abs(height(left) - height(right)) <= 1`.
- Rebalancing uses four classic cases:
  - LL -> single right rotation
  - RR -> single left rotation
  - LR -> left rotation on child, then right rotation on node
  - RL -> right rotation on child, then left rotation on node
- Deletion can trigger multiple repairs on the path back to the root, so validation after deletion matters as much as after insertion.

## Self-test
1. Why is AVL search still `O(log n)`? Because the strict balance invariant keeps tree height logarithmic in the number of nodes.
2. Which cases need double rotations? LR and RL.
3. Why recompute expected heights during validation? To catch stale metadata bugs after rotations or deletion transplants.
