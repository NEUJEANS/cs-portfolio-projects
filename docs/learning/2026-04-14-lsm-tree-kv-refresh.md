# Refresh + self-test: lsm-tree-kv

## Quick refresh
- WAL: append each mutation before considering it durable enough to recover
- memtable: the mutable in-memory structure that absorbs writes cheaply
- SSTable: immutable sorted table written during flush/compaction
- tombstone: a delete marker that must win over older values until compaction removes dead state
- compaction: merge immutable tables to reduce read amplification and remove obsolete entries

## Self-test
1. Why is an SSTable immutable?
   - So writes stay sequential and readers can reason about stable on-disk snapshots.
2. Why is a tombstone needed instead of deleting old values from every SSTable immediately?
   - Older tables are immutable, so deletes must be represented as a newer record that shadows older values until compaction.
3. What is the trade-off of postponing compaction?
   - Writes stay cheap, but reads may need to consult more tables.
4. Why is this project still useful even though it uses JSON files?
   - The storage-engine concepts remain visible and easy to explain without hiding them behind binary formats.
