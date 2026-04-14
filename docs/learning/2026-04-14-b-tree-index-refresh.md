# B-tree index lab refresh and self-test

## Quick refresh
- `bisect_left` is useful for locating the insertion/search slot within a node's sorted keys.
- Top-down insertion splits a full child before descending, which keeps the recursion simple.
- In-order traversal of a B-tree yields globally sorted keys.

## Self-test
1. If `t=2`, what is the maximum number of keys in a node? -> `2t-1 = 3`
2. Why split before descending? -> so the recursive call never receives a full node
3. Why are range queries natural here? -> keys stay ordered across leaves/subtrees
