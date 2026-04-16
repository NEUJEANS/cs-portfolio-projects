# B-Tree Index Lab

A compact B-tree indexing project that demonstrates top-down node splitting, sorted traversal, range queries, deletion rebalancing, serialized page snapshots, fixed-size binary page encoding, and build-time benchmarking for sorted bulk loads.

## Why it belongs in a CS portfolio
- shows understanding of balanced multi-way search trees used by databases and filesystems
- implements insertion and deletion with split/borrow/merge handling instead of relying on a library container
- includes ordered dumps and range queries to connect the data structure to indexing workloads
- persists and reloads the tree structure as JSON and as fixed-size binary pages to bridge in-memory algorithms with storage-oriented index design
- ships with automated tests and a small CLI for reproducible demos

## Features
- configurable minimum degree `t`
- insert/search with duplicate-key updates
- sorted traversal of all key/value pairs
- inclusive range queries for index-style lookups
- nearest-key navigation with floor/ceil and neighbor lookups
- deletion with predecessor/successor replacement and borrow/merge rebalancing
- JSON CLI output for demos and scripting
- append-oriented bulk loading for strictly sorted datasets
- tree snapshot/save/load support for serialized page inspection
- fixed-size binary page encoding with explicit page-layout validation and round-trip loading
- benchmark mode comparing generic inserts against sorted bulk loading on the same dataset

## Usage
```bash
python3 btree_index.py --dataset sample_records.json dump
python3 btree_index.py --dataset sample_records.json search 17
python3 btree_index.py --dataset sorted_records.json --bulk-load --json stats
python3 btree_index.py --dataset sorted_records.json --benchmark-repeats 10 --json benchmark-build
python3 btree_index.py --dataset sample_records.json --json range 10 30
python3 btree_index.py --dataset sample_records.json --json neighbors 16
python3 btree_index.py --dataset sample_records.json --json floor 16
python3 btree_index.py --dataset sample_records.json --json ceil 16
python3 btree_index.py --dataset sample_records.json --json delete 17
python3 btree_index.py --dataset sample_records.json --json snapshot
python3 btree_index.py --dataset sample_records.json --json save tree_snapshot.json
python3 btree_index.py --tree-file tree_snapshot.json --json search 17
python3 btree_index.py --dataset sample_records.json --page-size 256 --value-bytes 24 --json page-layout
python3 btree_index.py --dataset sample_records.json --page-size 256 --value-bytes 24 --json save-pages tree.pages
python3 btree_index.py --page-file tree.pages --json search 17
```

Dataset format:
```json
[
  {"key": 10, "value": "ten"},
  {"key": 20, "value": "twenty"}
]
```

Serialized tree format:
```json
{
  "minimum_degree": 2,
  "item_count": 4,
  "root": {
    "leaf": false,
    "keys": [9],
    "values": ["nine"],
    "children": [
      {"leaf": true, "keys": [1, 3], "values": ["one", "three"]},
      {"leaf": true, "keys": [14], "values": ["fourteen"]}
    ]
  }
}
```

Binary page format notes:
- `page-layout` reports whether a chosen page size can hold one node for the selected minimum degree.
- `save-pages` writes a compact binary file with a file header plus one fixed-size page per B-tree node.
- each value uses a fixed UTF-8 slot (`--value-bytes`, including a 2-byte length prefix), so oversized values fail fast instead of being truncated.

## Test
```bash
python3 -m unittest projects/b-tree-index-lab/test_btree_index.py
```

## Future improvements
- export benchmark results as CSV/JSON artifacts for README charts
- simple performance comparison against other ordered structures
- more space-efficient slotted-page encoding for variable-length values
