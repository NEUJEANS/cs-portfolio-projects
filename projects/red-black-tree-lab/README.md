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
- Graphviz DOT export for portfolio screenshots, blog posts, and balancing walkthrough diagrams
- deterministic benchmark mode that compares red-black and AVL tree height/rotation trade-offs on ascending, descending, and shuffled insert orders
- chart-ready benchmark CSV export for spreadsheet plots, README charts, or recruiter-facing artifacts
- CLI commands for demo runs, custom builds, membership queries, rank queries, kth-smallest lookup, deletion checks, DOT export, trace-to-Markdown walkthrough export, and cross-tree benchmarking

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

Export a Graphviz DOT diagram you can pipe into `dot -Tsvg` or paste into an online renderer:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py dot 20 10 30 5
python3 projects/red-black-tree-lab/red_black_tree.py dot --no-nil 20 10 30 5
```

Benchmark the red-black implementation against the repo's AVL tree lab on multiple insertion orders:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py benchmark --count 31 --seed 7
```

Embed chart-ready CSV in the JSON output or write it straight to a file for spreadsheet/chart tooling:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py benchmark --count 31 --seed 7 --csv
python3 projects/red-black-tree-lab/red_black_tree.py benchmark --count 31 --seed 7 --csv-file artifacts/red-black-vs-avl.csv
```

Include a trace of rotations and fix-up cases for portfolio walkthroughs:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py delete --trace 10 20 10 30 5 15 25 35
python3 projects/red-black-tree-lab/red_black_tree.py demo --trace
```

Generate a recruiter-friendly Markdown explanation from the same trace stream and optionally write it to a file. The exported walkthrough now embeds initial/final Graphviz DOT snippets so you can render before/after diagrams without rebuilding the tree by hand:

```bash
python3 projects/red-black-tree-lab/red_black_tree.py explain-trace build 10 20 30 15 25 5
python3 projects/red-black-tree-lab/red_black_tree.py explain-trace delete 20 10 30 5 15 25 35 --query 10 --output artifacts/red-black-delete-trace.md
```

## Test

```bash
python3 -m unittest tests/test_red_black_tree_lab.py
python3 projects/red-black-tree-lab/red_black_tree.py benchmark --count 31 --seed 7
python3 projects/red-black-tree-lab/red_black_tree.py benchmark --count 31 --seed 7 --csv-file artifacts/red-black-vs-avl.csv
```

## Design notes
- New nodes start red so existing black heights remain unchanged unless a red-red violation appears.
- Insertion repair follows the standard uncle-red recolor case and the inner/outer rotation cases.
- Deletion swaps with the inorder successor when needed, then runs double-black repair with sibling-color case analysis.
- Order-statistics support stores `subtree_size` on every node and refreshes it after path growth, transplants, and rotations.
- Validation explicitly checks BST bounds, black-height consistency, parent pointers, and subtree-size consistency so augmentation bugs stay explainable.
- Trace output names the repair cases that fired during insertion or deletion, making the balancing logic easier to narrate in a README, code review, or interview demo.
- The `explain-trace` command turns low-level trace events into a Markdown walkthrough so the project can produce portfolio-ready writeups without hand-editing every balancing step.
- `explain-trace` also embeds initial/final DOT snapshots in the exported Markdown, which makes before/after balancing diagrams easy to render directly from the walkthrough artifact.
- DOT export labels left/right child edges and can optionally render NIL leaves, which makes black-height explanations and deletion repair screenshots easier to present.
- The benchmark command intentionally uses deterministic ascending, descending, and seeded shuffled sequences so the AVL-vs-red-black comparison is repeatable in README snippets, interviews, and CI runs.
- CSV export keeps the case-level metrics flat and spreadsheet-friendly so the project can produce quick charts without extra post-processing glue code.

## Future improvements
- emit Graphviz diagrams after each insertion/deletion step
- extend the benchmark with CSV export for chart-ready artifacts across larger input sizes
- render trace-event snapshots as SVG/PNG assets directly from the walkthrough export pipeline
