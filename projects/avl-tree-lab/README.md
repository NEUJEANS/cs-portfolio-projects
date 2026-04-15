# avl-tree-lab

A portfolio-friendly AVL tree project that implements insertion, deletion, validation, traceable rotations, and order-statistics queries in a compact Python program.

## Why it is interesting
- demonstrates deterministic self-balancing search trees with a strict height guarantee
- makes AVL single and double rotations inspectable for interviews and code reviews
- shows how classic data-structure invariants can be encoded as validation logic instead of hand-wavy comments
- adds rank/select queries on top of the balanced tree for richer demos and comparisons with red-black trees
- gives strong material for discussing trade-offs between tighter balancing and rotation overhead

## Features
- integer-key AVL tree with duplicate rejection
- insertion and deletion with automatic LL, RR, LR, and RL rebalancing
- validation for BST ordering, stored heights, and balance-factor constraints
- inorder/preorder traversal helpers plus `contains`, `rank`, and `select`
- optional trace mode that records insert/delete events and rotation cases
- CLI commands for demo runs, custom builds, membership queries, deletion, and validation

## Usage

Run the bundled demo:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py demo --trace
```

Build a custom tree:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py build 30 20 10 25 40 50
```

Check membership:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py contains 25 30 20 10 25 40 50
```

Delete a key and inspect the repaired tree:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py delete 20 20 10 30 25 40 22 --trace
```

Count keys smaller than a query:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py rank 50 40 10 60 5 20 50 70
```

Return the zero-based kth smallest key:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py select 4 40 10 60 5 20 50 70
```

Validate a built tree:

```bash
python3 projects/avl-tree-lab/avl_tree_lab.py validate 30 20 10 25 40 50
```

## Test

```bash
python3 -m unittest projects/avl-tree-lab/test_avl_tree_lab.py
```

## Design notes
- AVL trees store subtree height on each node and keep the left/right height difference within `[-1, 1]`.
- Insertions and deletions rebalance on the way back up the recursion, which keeps the local repair logic small and inspectable.
- Double-rotation cases are logged in trace mode so the tree can be used as an interview walkthrough artifact.
- Validation recomputes expected heights recursively and reports invariant violations with explicit issue strings.
- `rank` and `select` are implemented via subtree-size recomputation, which keeps the code compact for a teaching project at the cost of extra query work.

## Future improvements
- maintain subtree sizes incrementally to make `rank` and `select` true `O(log n)` operations
- emit Graphviz diagrams for each rebalance step
- benchmark height and rotation counts against the repo's red-black and splay tree labs
