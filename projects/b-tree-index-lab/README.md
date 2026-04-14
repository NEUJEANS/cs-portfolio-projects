# B-Tree Index Lab

A compact B-tree indexing project that demonstrates top-down node splitting, sorted traversal, and range queries.

## Why it belongs in a CS portfolio
- shows understanding of balanced multi-way search trees used by databases and filesystems
- implements insertion with split handling instead of relying on a library container
- includes ordered dumps and range queries to connect the data structure to indexing workloads
- ships with automated tests and a small CLI for reproducible demos

## Features
- configurable minimum degree `t`
- insert/search with duplicate-key updates
- sorted traversal of all key/value pairs
- inclusive range queries for index-style lookups
- JSON CLI output for demos and scripting

## Usage
```bash
python3 btree_index.py --dataset sample_records.json dump
python3 btree_index.py --dataset sample_records.json search 17
python3 btree_index.py --dataset sample_records.json --json range 10 30
```

Dataset format:
```json
[
  {"key": 10, "value": "ten"},
  {"key": 20, "value": "twenty"}
]
```

## Test
```bash
python3 -m unittest projects/b-tree-index-lab/test_btree_index.py
```

## Future improvements
- deletion with borrow/merge rebalancing
- on-disk page serialization
- bulk loading from already sorted data
- simple performance comparison against other ordered structures
