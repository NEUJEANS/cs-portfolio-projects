# treap-order-statistics-lab

A portfolio-friendly randomized balanced BST project that combines treap split/merge mechanics with order-statistics queries such as rank, select, and inclusive range counting.

## Why it is interesting
- demonstrates how randomized priorities can keep a BST balanced without explicit rotations
- shows the split/merge formulation that powers many sequence and interval data-structure variants
- makes order-statistics practical by maintaining subtree sizes incrementally
- gives interview-ready material for comparing treaps with AVL, red-black, and splay trees
- stays compact enough to read end-to-end in one sitting

## Features
- deterministic seeded priorities for reproducible demos and tests
- insert and delete built on treap split/merge primitives
- `contains`, `rank`, `select`, and inclusive `range-count` queries
- validation for BST ordering, heap priorities, and stored subtree sizes
- trace mode that logs inserted priorities and deletions
- CLI commands for demo runs, custom builds, deletion, order-statistics queries, and validation

## Usage

Run the bundled demo:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 5 demo --trace
```

Build a custom treap:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 build 40 10 60 5 20 50 70
```

Delete a key and inspect the repaired treap:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 delete 60 40 10 60 5 20 50 70 --trace
```

Count keys smaller than a query:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 rank 50 40 10 60 5 20 50 70
```

Return the zero-based kth smallest key:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 select 3 40 10 60 5 20 50 70
```

Count keys inside an inclusive range:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 range-count 15 65 40 10 60 5 20 50 70
```

Validate a built treap:

```bash
python3 projects/treap-order-statistics-lab/treap_order_statistics_lab.py --seed 12 validate 40 10 60 5 20 50 70
```

## Test

```bash
python3 -m unittest projects/treap-order-statistics-lab/test_treap_order_statistics_lab.py
```

## Design notes
- each node stores a random priority plus subtree size, which makes balance probabilistic and order-statistics exact
- insertion promotes a new node when its priority beats the current root, then reuses split to partition the older subtree
- deletion removes a key by merging its left and right children, keeping the implementation compact
- validation recomputes subtree sizes and checks heap-order constraints so invariants are inspectable rather than assumed
- deterministic seeds make the project teachable, benchmarkable, and easier to compare across runs

## Future improvements
- add Graphviz or Mermaid export for split/merge traces
- benchmark height and query latency against the repo's AVL, red-black, and splay tree labs
- extend the node payload from keys to `(key, value)` pairs for map-style use cases
