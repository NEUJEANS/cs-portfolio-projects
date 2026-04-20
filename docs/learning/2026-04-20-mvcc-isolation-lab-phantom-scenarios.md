# MVCC isolation lab phantom slice refresh + self-test — 2026-04-20

## Quick refresh
- a phantom anomaly happens when a transaction re-checks a predicate (or would have re-checked it) and the matching row set changed because another transaction inserted, deleted, or reclassified rows
- key-based read-set validation catches direct overlap on rows that already existed, but it misses inserts into a previously-empty matching range
- one compact teaching fix is to remember the predicate that a transaction scanned and compare the matching set at commit time against the transaction snapshot

## Self-test
1. Why can snapshot isolation still allow a double-booking phantom?
   - because both transactions can scan an empty slot, write different reservation rows, and avoid direct write-write conflict on the same key
2. What should the lab store from a `scan` step besides the count alias?
   - enough predicate metadata to reconstruct the scanned range/filter during serializable validation
3. Why keep the scan DSL to key-prefix matching instead of adding a full query language?
   - it keeps the project dependency-free, deterministic, and easy to explain in interviews while still demonstrating the anomaly clearly

## Guardrails
- keep existing `read` / `assert` / `write` scenarios fully compatible
- make the phantom example deterministic and small enough that the committed Markdown/SVG artifacts stay readable
- document that this is still a compact teaching model, not a full database engine with real predicate locks
