# Treap order-statistics refresh

## Refresher
- `split(root, key)` returns `<= key` on the left and `> key` on the right.
- `merge(left, right)` requires every key in `left` to be smaller than every key in `right`.
- Store subtree sizes on each node so `rank` and `select` stay `O(log n)` on expected-height trees.
- Seeded RNG is useful for deterministic tests even when the balancing strategy is randomized.

## Self-test
1. Why does deleting a node reduce to `merge(node.left, node.right)`?
   - Because both subtrees already satisfy BST ordering around the deleted key; merge restores the heap ordering while preserving sorted order.
2. How do you count keys in `[L, R]`?
   - Compute `rank(R + 1) - rank(L)` for integer keys.
3. What extra invariant must validation check beyond ordinary BST rules?
   - Parent priorities must be at least as large as child priorities, and stored subtree sizes must match recomputed sizes.
