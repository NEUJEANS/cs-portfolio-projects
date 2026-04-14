# wal-kv-store

## Overview
A local write-ahead-log-backed key-value store that demonstrates append-only persistence, replay recovery, tombstone deletes, and checkpoint-based compaction.

## Why it is portfolio-worthy
- shows storage-engine fundamentals in a small, runnable project
- demonstrates durable append-only mutation logs and startup recovery
- includes tombstones and compaction, which are great interview discussion hooks
- stays simple enough to inspect end-to-end without hand-wavy magic

## Stack
- Python 3
- JSON Lines for the WAL file format
- JSON snapshot files for checkpoints
- `unittest` for behavior and CLI tests

## Features
- append-only `set` and `delete` operations with monotonically increasing sequence numbers
- crash-friendly replay recovery from WAL plus optional snapshot bootstrap
- tombstone deletes that survive reloads
- checkpoint command that compacts current live state into a snapshot and resets the active WAL
- CLI commands for `set`, `get`, `delete`, `list`, `history`, `stats`, and `checkpoint`
- delete responses report whether the key existed before the tombstone was written
- checkpointing intentionally compacts away prior mutation history so reload semantics stay predictable

## Usage
Set a key:

```bash
python3 wal_kv_store.py --dir demo-data set course cs5100
```

Get a key:

```bash
python3 wal_kv_store.py --dir demo-data get course
```

Inspect current items:

```bash
python3 wal_kv_store.py --dir demo-data list
```

Delete a key:

```bash
python3 wal_kv_store.py --dir demo-data delete course
```

Inspect mutation history for one key:

```bash
python3 wal_kv_store.py --dir demo-data history course
```

Compact the store into a snapshot:

```bash
python3 wal_kv_store.py --dir demo-data checkpoint
```

View storage stats:

```bash
python3 wal_kv_store.py --dir demo-data stats
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- checksums and corruption detection for WAL records
- fsync / durability modes for stricter crash guarantees
- sorted indexes or range queries
- multi-table namespaces and background compaction
- HTTP or gRPC wrapper for remote access
