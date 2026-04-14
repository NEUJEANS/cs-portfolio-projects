# Review pass 2: lsm-tree-kv

## Focus
Observability and portfolio presentation.

## Findings
- `stats` only exposed counts, which undersold the storage-engine angle.
- There was no quick way to see how much data still lived in the WAL versus immutable tables.

## Fixes applied
- extended `stats()` to report `wal_bytes` and aggregated `sstable_bytes`
- updated the README feature list so the new visibility is documented
- re-ran the project test suite after the change
