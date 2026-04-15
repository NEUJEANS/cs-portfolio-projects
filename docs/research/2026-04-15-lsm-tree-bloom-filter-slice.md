# LSM Tree Bloom Filter Slice Research

Date: 2026-04-15

## Goal
Add a compact, portfolio-friendly Bloom filter layer to the existing `lsm-tree-kv` project so negative lookups can skip SSTable loads.

## Brief research summary
A quick review of LSM-tree Bloom filter guidance highlighted the usual pattern:
- attach one Bloom filter per SSTable
- check the filter before opening or parsing the table on reads
- tune bits-per-key to trade memory for fewer false positives
- keep the guarantee of **no false negatives**, which makes SSTable skipping safe for negative lookups

## Sources consulted
- Gemini web search synthesis for “LSM tree bloom filters negative lookup SSTable skip”
- high-signal references surfaced in results included RocksDB/LevelDB-oriented material and the Monkey LSM-tree paper discussion

## Implementation decision for this slice
For this repo, keep the feature intentionally simple and teachable:
- store Bloom filter metadata directly inside each JSON SSTable file
- use SHA-256-derived double hashing to generate bit positions
- keep existing sorted-entry SSTable format intact
- expose Bloom filter footprint in `stats`
- add tests that prove negative lookups can reject an SSTable without loading its entries

## Why this is a good portfolio slice
It strengthens the storage-engine story without turning the project into a full database internals codebase. A student can now explain:
- WAL + memtable + SSTables
- tombstones and compaction
- why negative lookups are expensive
- how Bloom filters reduce unnecessary SSTable reads
