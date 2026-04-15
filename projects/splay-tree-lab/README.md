# splay-tree-lab

A portfolio-ready Python lab for splay trees: self-adjusting binary search trees that move recently accessed keys toward the root.

## Why it is interesting
- demonstrates amortized analysis in a concrete, runnable data structure
- shows how access patterns can matter as much as worst-case big-O tables
- gives you a compact lab to discuss zig, zig-zig, and zig-zag rotations in interviews
- stays practical with snapshot files, CLI demos, and deterministic tests

## Features
- build a splay tree snapshot from newline-delimited integers
- run access sequences and inspect hit/miss, root movement, and rotation counts
- insert and delete keys while keeping snapshots resumable
- deterministic unit tests for tree behavior and CLI workflows

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

Inspect the current summary:

```bash
python3 splay_tree_lab.py show --snapshot artifacts/splay-pruned.json
```

## Test

```bash
python3 -m unittest projects/splay-tree-lab/test_splay_tree_lab.py
```

## Future improvements
- add split and join subcommands for a fuller self-adjusting-tree toolkit
- export Graphviz or Mermaid diagrams for before/after access sequences
- add a benchmark that compares skewed workloads against red-black or AVL trees
