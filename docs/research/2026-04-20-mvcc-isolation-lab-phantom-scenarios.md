# MVCC isolation lab phantom-scenario research — 2026-04-20

## Why this slice
The lab already covered write skew and repeatable reads, but it still lacked a scenario where the dangerous overlap is a predicate/range scan instead of a direct key read. Adding one makes the project tell a fuller isolation story for database interviews and portfolio walkthroughs.

## Brief source notes
1. PostgreSQL transaction isolation docs (`https://www.postgresql.org/docs/current/transaction-iso.html`)
   - the SQL-standard anomaly list explicitly calls out **phantom read**: rerunning a query can return a different set of rows after another transaction commits
   - `Read Committed` may show phantom reads, while `Serializable` is defined to prevent serialization anomalies
2. Isolation / phantom-read overview (`https://en.wikipedia.org/wiki/Phantom_read`)
   - phantoms are about the membership of a matching row set changing, not only a previously-read key changing value
   - classic serializability mechanisms therefore need predicate-aware protection (for example predicate locks or equivalent validation), not only point-key conflict checks

## Design takeaway for this lab
- keep the DSL small by modeling predicate reads as a deterministic `scan` over key prefixes instead of adding a full SQL parser
- keep `snapshot` intentionally weak here so students can see why write-write conflict checks alone do **not** stop predicate anomalies
- extend the teaching `serializable` validator with predicate-result comparison at commit time so the phantom story is visible in one repo-local scenario without pretending to implement a full vendor-specific SSI engine
