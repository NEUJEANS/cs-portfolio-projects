# B-Tree Index Lab

A compact B-tree indexing project that demonstrates top-down node splitting, sorted traversal, range queries, deletion rebalancing, and serialized page snapshots.

## Why it belongs in a CS portfolio
- shows understanding of balanced multi-way search trees used by databases and filesystems
- implements insertion and deletion with split/borrow/merge handling instead of relying on a library container
- includes ordered dumps and range queries to connect the data structure to indexing workloads
- persists and reloads the tree structure as JSON to bridge in-memory algorithms with storage-oriented index design
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

## Usage
```bash
python3 btree_index.py --dataset sample_records.json dump
python3 btree_index.py --dataset sample_records.json search 17
python3 btree_index.py --dataset sorted_records.json --bulk-load --json stats
python3 btree_index.py --dataset sample_records.json --json range 10 30
python3 btree_index.py --dataset sample_records.json --json neighbors 16
python3 btree_index.py --dataset sample_records.json --json floor 16
python3 btree_index.py --dataset sample_records.json --json ceil 16
python3 btree_index.py --dataset sample_records.json --json delete 17
python3 btree_index.py --dataset sample_records.json --json snapshot
python3 btree_index.py --dataset sample_records.json --json save tree_snapshot.json
python3 btree_index.py --tree-file tree_snapshot.json --json search 17
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

## Test
```bash
python3 -m unittest projects/b-tree-index-lab/test_btree_index.py
```

## Future improvements
- benchmark bulk loading against generic inserts on larger synthetic datasets
- simple performance comparison against other ordered structures
- optional fixed-size on-disk page encoding beyond JSON snapshots
