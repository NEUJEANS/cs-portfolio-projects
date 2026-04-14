# WAL KV Store Refresh + Self-Test

## Concepts refreshed
- write-ahead log: append mutations before they are considered durable state
- replay recovery: reconstruct the latest state by applying log records in order
- tombstone: a delete marker kept in the log so recovery knows the key was removed
- checkpoint / compaction: materialize current state and discard superseded history from the active WAL

## Quick self-test
1. Why keep deletes as tombstones in the log?
   - So replay can correctly preserve the fact that a key was deleted, even though older set records still exist earlier in the log.
2. Why is replay order important?
   - Because later records override earlier ones; without total order, recovered state is ambiguous.
3. What does checkpointing buy us?
   - Faster startup and smaller active logs because we no longer need to replay the full mutation history every time.
4. What is intentionally out of scope here?
   - Concurrent writers, checksums, page layouts, and full crash-consistency guarantees across power loss.
