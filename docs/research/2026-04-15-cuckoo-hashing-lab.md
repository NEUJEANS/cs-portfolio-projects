# 2026-04-15 Cuckoo hashing lab research

## Brief notes
- Cuckoo hashing is portfolio-friendly because it turns collision handling into a concrete, visualizable story: each key has two candidate homes and insertion may kick another key to its alternate home.
- The interesting engineering edge is not lookup but insertion under pressure: bounded displacement attempts need a fallback path, usually rehashing with a larger table or new hash functions.
- For a compact student project, a single-slot table with two hash functions, snapshot export, and deterministic tests is enough to discuss worst-case O(1) lookup, load factor tradeoffs, and cycle handling in interviews.

## Slice choice
- The repo already covers many strong structures, so adding a new hashing-focused lab is more valuable than polishing an already polished project.
- This slice will create a new `cuckoo-hashing-lab` with a CLI, saved snapshots, removal/export flows, and tests that intentionally force rehashing.
