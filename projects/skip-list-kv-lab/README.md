# Skip List KV Lab

A Python skip-list-backed ordered key/value store with search, insert, delete, range queries, persistence, and stats output.

## Why this project matters
Skip lists are a classic probabilistic data structure that offer expected `O(log n)` search, insertion, and deletion while keeping an implementation simpler than a balanced tree. This makes them a strong portfolio project for showing ordered indexing, randomized algorithms, and careful data-structure testing.

## Features
- probabilistic multi-level linked structure with configurable promotion probability
- ordered insert, update, lookup, and delete operations
- range query support over sorted string keys
- JSON-backed CLI with `get`, `put`, `delete`, `range`, `dump`, and `stats`
- deterministic seeds for reproducible demos and tests
- focused tests for data-structure behavior and CLI persistence

## Files
- `skip_list_kv.py` - implementation + CLI
- `sample_pairs.json` - demo dataset
- `test_skip_list_kv.py` - unittest suite

## Usage
Dump all items in key order:

```bash
python3 projects/skip-list-kv-lab/skip_list_kv.py \
  projects/skip-list-kv-lab/sample_pairs.json \
  dump
```

Run a range query:

```bash
python3 projects/skip-list-kv-lab/skip_list_kv.py \
  projects/skip-list-kv-lab/sample_pairs.json \
  range --start banana --stop fig
```

Insert a new key and persist it back to disk:

```bash
python3 projects/skip-list-kv-lab/skip_list_kv.py \
  projects/skip-list-kv-lab/sample_pairs.json \
  put eggplant '{"qty": 2, "aisle": 4}' --persist
```

Inspect height distribution and active levels:

```bash
python3 projects/skip-list-kv-lab/skip_list_kv.py \
  projects/skip-list-kv-lab/sample_pairs.json \
  stats
```

Run tests:

```bash
python3 -m unittest -q projects/skip-list-kv-lab/test_skip_list_kv.py
```

## Architecture notes
1. The head node stores forward pointers for every possible level.
2. Each inserted node gets a random height from repeated coin flips up to `max_level`.
3. Searches walk right while the next key is still smaller, then drop down one level.
4. Range queries reuse the skip-list search path to jump close to the lower bound before scanning level 0.

## Future improvements
- support custom comparators or integer-key optimized storage
- add merge/join operations for two ordered skip lists
- add benchmarking against `bisect`-backed arrays and tree-based maps
- support TTL metadata or disk-backed segments for a larger storage lab
