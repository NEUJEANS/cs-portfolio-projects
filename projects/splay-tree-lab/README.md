# splay-tree-lab

A portfolio-ready Python lab for splay trees: self-adjusting binary search trees that move recently accessed keys toward the root.

## Why it is interesting
- demonstrates amortized analysis in a concrete, runnable data structure
- shows how access patterns can matter as much as worst-case big-O tables
- gives you a compact lab to discuss zig, zig-zig, and zig-zag rotations in interviews
- stays practical with snapshot files, CLI demos, deterministic tests, and a cross-project benchmark against the red-black tree lab

## Features
- build a splay tree snapshot from newline-delimited integers
- run access sequences and inspect hit/miss, root movement, and rotation counts
- insert and delete keys while keeping snapshots resumable
- split a tree around a pivot and join two disjoint sorted value sets into a new snapshot
- benchmark skewed hot-set lookups against the `red-black-tree-lab` baseline using deterministic comparison counts
- deterministic unit tests for tree behavior, CLI workflows, and benchmark output

## Usage

Build a snapshot:

```bash
python3 splay_tree_lab.py build --input sample_values.txt --output artifacts/splay.json
```

Run an access sequence:

```bash
python3 splay_tree_lab.py access --snapshot artifacts/splay.json --output artifacts/splay-hot.json 7 7 3 18 99
```

Insert a new key:

```bash
python3 splay_tree_lab.py insert --snapshot artifacts/splay-hot.json --output artifacts/splay-grown.json 11
```

Delete a key:

```bash
python3 splay_tree_lab.py delete --snapshot artifacts/splay-grown.json --output artifacts/splay-pruned.json 3
```

Split the current tree around a pivot (left side is `< pivot`, right side is `> pivot` when present):

```bash
python3 splay_tree_lab.py split --snapshot artifacts/splay-pruned.json 11
```

Join two sorted, disjoint value sets into a new tree snapshot:

```bash
python3 splay_tree_lab.py join --left-input left_values.txt --right-input right_values.txt --output artifacts/splay-joined.json
```

Inspect the current summary:

```bash
python3 splay_tree_lab.py show --snapshot artifacts/splay-pruned.json
```

Compare hot-set and uniform-random workloads against the red-black tree lab:

```bash
python3 splay_tree_lab.py benchmark --size 255 --hot-set-size 8 --hot-queries 256 --random-queries 256 --seed 42
```

## Test

```bash
python3 -m unittest projects/splay-tree-lab/test_splay_tree_lab.py
```

## Benchmark interpretation
- the benchmark reports key-comparison counts instead of wall-clock time so the output stays deterministic and testable
- positive `hotset_comparison_gap` means the splay tree used fewer comparisons than the red-black baseline on repeated hot-key accesses
- uniform-random workloads may reduce or reverse the gap, which helps explain the trade-off between self-adjusting behavior and steadier balancing

## Future improvements
- export Graphviz or Mermaid diagrams for before/after access sequences
- add split/join snapshot artifact helpers that persist both sides directly for larger scripted demos
