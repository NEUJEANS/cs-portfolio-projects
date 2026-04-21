# Research — library-manager-sqlite FTS search — 2026-04-21

## Goal
Find the smallest meaningful search upgrade that makes `library-manager-sqlite` feel more like a CS/data-systems portfolio piece instead of a basic CRUD demo.

## Sources checked
- SQLite FTS5 docs: `https://www.sqlite.org/fts5.html`
- SQLite trigger docs: `https://www.sqlite.org/lang_createtrigger.html`

## Notes
- FTS5 ships with modern SQLite builds and supports `MATCH`, ranked ordering via `ORDER BY rank`/`bm25(...)`, plus phrase/prefix queries.
- For this project, a small dedicated FTS table is enough; we do not need a full external-content setup yet because catalog title/author metadata is append-only in the current CLI.
- Old databases need a one-time backfill so the search index is immediately useful after migration.
- Highlight/snippet helpers make the CLI output visibly stronger for demos and recruiter walkthroughs.

## Decision
Implement an FTS-backed catalog search path with:
- automatic index creation when FTS5 is available
- one-time backfill for existing books
- automatic fallback to the existing substring search path when FTS5 is unavailable
- phrase/prefix-friendly querying and ranked results
