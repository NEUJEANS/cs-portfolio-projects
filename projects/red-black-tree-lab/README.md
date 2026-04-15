# red-black-tree-lab

A portfolio-friendly balanced tree lab that implements red-black tree insertion, validates invariants, and exposes a small CLI for deterministic demos.

## Why it is interesting
- demonstrates a classic self-balancing BST used in standard libraries, database indexes, and schedulers
- makes rotation and recoloring logic inspectable instead of hiding it behind a container type
- turns abstract invariants into testable validation output
- gives strong interview material around balancing guarantees and fix-up cases

## Features
- integer-key red-black tree with duplicate rejection
- left/right rotations and insertion fix-up cases
- inorder traversal, height, black-height, and search helpers
- validation report for BST ordering and red-black invariants
- CLI commands for demo runs, custom builds, and membership queries

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

## Test

```bash
python3 -m unittest tests/test_red_black_tree_lab.py
```

## Design notes
- New nodes start red so existing black heights remain unchanged unless a red-red violation appears.
- Repair follows the standard uncle-red recolor case and the inner/outer rotation cases.
- Validation explicitly checks BST bounds and black-height consistency so the project stays explainable.

## Future improvements
- add deletion with double-black repair cases
- emit Graphviz diagrams after each insertion step
- benchmark against AVL trees for height and rotation counts
