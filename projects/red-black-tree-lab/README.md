# red-black-tree-lab

A portfolio-friendly balanced tree lab that implements red-black tree insertion, validates invariants, and now exposes order-statistics queries for deterministic demos.

## Why it is interesting
- demonstrates a classic self-balancing BST used in standard libraries, database indexes, and schedulers
- makes rotation and recoloring logic inspectable instead of hiding it behind a container type
- turns abstract invariants into testable validation output
- shows how balanced trees can be augmented for rank/select queries without changing asymptotic guarantees
- gives strong interview material around balancing guarantees, fix-up cases, and metadata-safe rotations

## Features
- integer-key red-black tree with duplicate rejection
- left/right rotations and insertion fix-up cases
- subtree-size augmentation for order-statistics operations
- inorder traversal, height, black-height, `rank`, `select`, and search helpers
- validation report for BST ordering, red-black invariants, and subtree-size consistency
- CLI commands for demo runs, custom builds, membership queries, rank queries, and kth-smallest lookup

## Usage

Run the bundled demo:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py demo
```

Build a custom tree:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py build 10 20 30 15 25 5
```

Check whether a key exists after building a tree:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py contains 15 10 20 30 15 25 5
```

Count how many keys are smaller than a query:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py rank 16 10 20 30 15 25 5
```

Return the zero-based kth smallest key:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py select 4 10 20 30 15 25 5
```

## Test

```bash
python3 -m unittest tests/test_red_black_tree_lab.py
```

## Design notes
- New nodes start red so existing black heights remain unchanged unless a red-red violation appears.
- Repair follows the standard uncle-red recolor case and the inner/outer rotation cases.
- Order-statistics support stores `subtree_size` on every node and refreshes it after path growth and rotations.
- Validation explicitly checks BST bounds, black-height consistency, parent pointers, and subtree-size consistency so augmentation bugs stay explainable.

## Future improvements
- add deletion with double-black repair cases
- emit Graphviz diagrams after each insertion step
- benchmark against AVL trees for height and rotation counts
