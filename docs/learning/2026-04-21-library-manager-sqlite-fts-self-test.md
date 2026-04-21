# Learning/self-test — library-manager-sqlite FTS slice — 2026-04-21

## Refresh target
SQLite FTS5 basics for a Python CLI project.

## Quick refresh
- create index table: `CREATE VIRTUAL TABLE ... USING fts5(...)`
- query with `MATCH ?`
- rank with `bm25(...)`
- expose visible matches with `highlight(...)`
- keep old data searchable by backfilling rows into the FTS table

## Self-test
Ran a one-off Python/SQLite smoke test in `:memory:`:
- created an FTS5 virtual table
- inserted a sample book row
- queried it with `MATCH 'distributed'`
- confirmed the local Python SQLite build supports FTS5

## Outcome
Safe to use FTS5 directly in this repo while still preserving a fallback path for portability.
