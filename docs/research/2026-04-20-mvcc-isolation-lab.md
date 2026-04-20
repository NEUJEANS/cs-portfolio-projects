# MVCC isolation lab research — 2026-04-20

## Why this slice
The repository already has strong algorithm/data-structure coverage, but it did not yet have a compact database-concurrency project. A small MVCC isolation simulator adds breadth in databases and systems design without needing a heavyweight external dependency.

## Brief source notes
1. PostgreSQL transaction isolation docs (`https://www.postgresql.org/docs/current/transaction-iso.html`)
   - `Read Committed` gives each statement a fresh committed snapshot, so successive reads in one transaction can see different committed states.
   - PostgreSQL documents `Serializable` as the mode that prevents serialization anomalies, while weaker modes may still permit them.
2. Snapshot isolation overview (`https://en.wikipedia.org/wiki/Snapshot_isolation`)
   - Snapshot isolation typically reads from a start-of-transaction snapshot and only rejects overlapping write-write conflicts.
   - Write skew is the classic anomaly where concurrent transactions update disjoint rows after reading the same stale invariant boundary.

## Design takeaway for this lab
- include `read-committed` so the simulator can show statement-level snapshot changes
- include `snapshot` so the doctor-on-call example can demonstrate write skew
- include a simple optimistic `serializable` validator that aborts when keys in the transaction's read or write set changed since its snapshot, which is enough to teach why serializable must be stricter than snapshot isolation
- document clearly that the serializable mode is a compact teaching model, not a byte-for-byte implementation of PostgreSQL SSI
