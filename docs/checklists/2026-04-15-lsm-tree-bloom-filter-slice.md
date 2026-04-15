# Checklist — lsm-tree-kv Bloom Filter Slice

Date: 2026-04-15
Project: `lsm-tree-kv`

- [x] inspect current LSM tree implementation and identify the weakest next systems upgrade
- [x] do brief Bloom filter / LSM read-path research
- [x] refresh Bloom filter correctness and double-hashing basics
- [x] design a small SSTable-embedded Bloom filter format
- [x] implement Bloom filter generation during flush/compaction
- [x] gate SSTable reads with range checks + Bloom filter membership checks
- [x] expose Bloom filter footprint in stats
- [x] add regression tests for persistence and negative-lookup skipping
- [x] update README with the new capability and usage notes
- [x] run targeted tests
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push safely
- [x] append wrap-up note
