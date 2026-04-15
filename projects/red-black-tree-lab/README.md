# red-black-tree-lab

A portfolio-friendly balanced tree lab that implements red-black tree insertion and deletion, validates invariants, and exposes order-statistics queries for deterministic demos.

## Why it is interesting
- demonstrates a classic self-balancing BST used in standard libraries, database indexes, and schedulers
- makes rotation and recoloring logic inspectable instead of hiding it behind a container type
- turns abstract invariants into testable validation output
- shows how balanced trees can be augmented for rank/select queries without changing asymptotic guarantees
- demonstrates the harder deletion side of the data structure, including double-black repair and successor replacement
- gives strong interview material around balancing guarantees, fix-up cases, deletion repair, and metadata-safe rotations

## Features
- integer-key red-black tree with duplicate rejection
- left/right rotations plus insertion and deletion fix-up cases
- inorder-successor deletion path with double-black repair support
- subtree-size augmentation for order-statistics operations
- inorder traversal, height, black-height, `rank`, `select`, delete, and search helpers
- validation report for BST ordering, red-black invariants, parent pointers, and subtree-size consistency
- optional trace mode that records insert/delete fix-up cases and rotations for explainable debugging demos
- CLI commands for demo runs, custom builds, membership queries, rank queries, kth-smallest lookup, and deletion checks

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

Delete a key and inspect the repaired tree:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py delete 10 20 10 30 5 15 25 35
```

Include a trace of rotations and fix-up cases for portfolio walkthroughs:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py delete --trace 10 20 10 30 5 15 25 35
python3 projects/red-black-tree-lab/red_black_tree.py demo --trace
```

## Test

```bash
python3 -m unittest tests/test_red_black_tree_lab.py
```

## Design notes
- New nodes start red so existing black heights remain unchanged unless a red-red violation appears.
- Insertion repair follows the standard uncle-red recolor case and the inner/outer rotation cases.
- Deletion swaps with the inorder successor when needed, then runs double-black repair with sibling-color case analysis.
- Order-statistics support stores `subtree_size` on every node and refreshes it after path growth, transplants, and rotations.
- Validation explicitly checks BST bounds, black-height consistency, parent pointers, and subtree-size consistency so augmentation bugs stay explainable.
- Trace output names the repair cases that fired during insertion or deletion, making the balancing logic easier to narrate in a README, code review, or interview demo.

## Future improvements
- emit Graphviz diagrams after each insertion/deletion step
- benchmark against AVL trees for height and rotation counts
- add a compact trace-to-markdown explainer that turns raw events into a narrated balancing walkthrough
