# lsm-tree-kv

## Overview
A compact Python key-value store that demonstrates the core ideas behind an LSM tree: a write-ahead log, an in-memory memtable, immutable SSTables, tombstone deletes, and manual compaction.

## Why it is portfolio-worthy
- shows storage-engine concepts that map to systems interviews and database internals courses
- keeps the implementation small enough to explain line-by-line during a project walkthrough
- demonstrates durability and recovery behavior instead of being just an in-memory toy
- leaves clear room for advanced follow-up work like Bloom filters, sparse indexes, and background compaction

## Stack
- Python 3
- JSON Lines WAL records
- JSON SSTable snapshots
- `unittest` for behavior and CLI coverage

## Features
- append-only WAL for every mutation
- startup recovery that replays the WAL into the memtable
- configurable memtable flush threshold
- immutable SSTables written on flush
- tombstone deletes that hide older values across reloads
- manual compaction that merges many SSTables into one live snapshot
- storage stats including WAL and SSTable byte totals
- CLI commands for `set`, `get`, `delete`, `list`, `stats`, `flush`, and `compact`

## Usage
Set a key:

```bash
python3 lsm_tree_kv.py --dir demo-data set project lsm-tree
```

Read a key:

```bash
python3 lsm_tree_kv.py --dir demo-data get project
```

Inspect live items:

```bash
python3 lsm_tree_kv.py --dir demo-data list
```

Force a memtable flush:

```bash
python3 lsm_tree_kv.py --dir demo-data --flush-threshold 2 flush
```

Compact SSTables:

```bash
python3 lsm_tree_kv.py --dir demo-data compact
```

Delete a key and report whether it previously existed:

```bash
python3 lsm_tree_kv.py --dir demo-data delete project
```

Show stats:

```bash
python3 lsm_tree_kv.py --dir demo-data stats
```

## Test
```bash
python3 -m unittest discover -s projects/lsm-tree-kv -p 'test_*.py'
```

## Future Improvements
- add binary search plus sparse indexes so SSTable lookups avoid full JSON loads
- add Bloom filters per SSTable to skip negative lookups quickly
- support value sizes large enough to justify block-based table layouts
- add background compaction policies and leveled/tiered strategies
- expose a small HTTP API for remote experiments
