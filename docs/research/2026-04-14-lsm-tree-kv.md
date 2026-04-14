# Research notes: lsm-tree-kv

## Why this project now
The existing repo already covers many CLIs, algorithms, and small systems labs. A compact LSM-tree-inspired store adds database/storage-engine depth and gives a strong interview discussion topic that is different from the existing WAL-only key-value store.

## Minimal vertical slice chosen
For this run, the goal is not a production-grade engine. The goal is a clear, runnable slice that demonstrates:
- append-only writes through a WAL
- an in-memory memtable holding latest dirty keys
- immutable SSTables created on flush
- tombstone deletes that suppress stale values in older tables
- manual compaction to merge live state into one SSTable

## Deliberate simplifications
- JSON is used instead of binary blocks so the data files are easy to inspect
- lookups scan SSTables instead of using Bloom filters or sparse indexes
- compaction is explicit and synchronous
- the memtable tracks latest entries by key rather than every historical mutation

## Next directions if expanded later
- sparse indexes and binary-searchable blocks
- per-SSTable Bloom filters for negative lookups
- background compaction heuristics
- benchmark scripts comparing flush thresholds and table counts
