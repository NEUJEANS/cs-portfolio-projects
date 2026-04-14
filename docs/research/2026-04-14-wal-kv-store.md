# WAL KV Store Research Notes

## Goal
Build a portfolio-friendly storage project that demonstrates append-only durability, crash recovery by log replay, deletion via tombstones, and checkpoint/compaction.

## Practical design choices
- Use a JSON Lines write-ahead log so the file format stays readable in interviews and code reviews.
- Treat each mutation as an immutable record with sequence numbers and timestamps.
- Recover by replaying the WAL from start to finish.
- Represent deletions as tombstones instead of in-place mutation.
- Support checkpointing by writing the current state into a compact snapshot plus a fresh WAL.

## Scope for this slice
- single-process local CLI
- commands for set/get/delete/list/history/stats/checkpoint
- replay-based recovery
- snapshot compaction that preserves current logical state
- unit tests for recovery, tombstones, and checkpointing

## Why it is portfolio-worthy
- touches storage-engine concepts without requiring a full database
- easy to demo from the terminal
- opens good follow-up discussion about indexing, fsync, crash safety, and SSTables/LSM trees

## Deferred ideas
- checksums and corruption handling
- namespaces / multiple tables
- range scans with sorted indexes
- background compaction worker
- HTTP wrapper for remote access
