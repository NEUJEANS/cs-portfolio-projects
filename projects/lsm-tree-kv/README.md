# lsm-tree-kv

## Overview
A compact Python key-value store that demonstrates the core ideas behind an LSM tree: a write-ahead log, an in-memory memtable, immutable SSTables, tombstone deletes, manual compaction, and per-SSTable Bloom filters for faster negative lookups.

## Why it is portfolio-worthy
- shows storage-engine concepts that map to systems interviews and database internals courses
- keeps the implementation small enough to explain line-by-line during a project walkthrough
- demonstrates durability and recovery behavior instead of being just an in-memory toy
- now includes Bloom-filter-assisted reads, which makes the read path feel closer to a real storage engine
- still leaves room for advanced follow-up work like sparse indexes and background compaction

## Stack
- Python 3
- JSON Lines WAL records
- JSON SSTable snapshots with embedded Bloom filter metadata
- `unittest` for behavior and CLI coverage

## Features
- append-only WAL for every mutation
- startup recovery that replays the WAL into the memtable
- configurable memtable flush threshold
- immutable SSTables written on flush
- per-SSTable Bloom filters plus min/max key guards to skip impossible reads early
- tombstone deletes that hide older values across reloads
- manual compaction that merges many SSTables into one live snapshot
- storage stats including WAL bytes, SSTable bytes, and Bloom filter footprint
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

Tune Bloom filter density while keeping the file format inspectable:

```bash
python3 lsm_tree_kv.py --dir demo-data --bloom-bits-per-key 12 stats
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

## What changed in the Bloom filter slice
- every flushed or compacted SSTable now stores Bloom filter metadata
- `get` checks `min_key` / `max_key` and the Bloom filter before loading the SSTable entries
- `stats` reports Bloom filter counts and total bits across current SSTables
- tests cover Bloom filter persistence and negative lookups that avoid loading SSTable contents

## Future Improvements
- add binary search plus sparse indexes so SSTable lookups avoid full JSON loads when Bloom filters pass
- support value sizes large enough to justify block-based table layouts
- add background compaction policies and leveled/tiered strategies
- expose a small HTTP API for remote experiments
- compare multiple bits-per-key settings with a benchmark harness and false-positive report
