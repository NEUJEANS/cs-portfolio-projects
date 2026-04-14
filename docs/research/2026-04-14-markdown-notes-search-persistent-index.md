# markdown-notes-search persistent index notes

Date: 2026-04-14
Project: `markdown-notes-search`

## Goal
Add a lightweight persistent index so repeated CLI searches do not need to fully reparse unchanged Markdown notes on every run.

## Brief research summary
- For a simple local CLI, a JSON cache is enough for a strong portfolio slice; full search-engine storage formats would be overkill.
- The safest minimal invalidation signal is a file signature such as `(mtime, size)` so unchanged files can be reused without hashing every file again.
- Incremental refresh should handle three cases cleanly: unchanged files reuse cache, changed/new files are reparsed, and deleted files disappear from the persisted index.
- Rebuild support matters for debugging and demos because it gives a deterministic recovery path when cache contents are suspected to be stale.

## Design choice for this slice
- store cached note records in a JSON file near the notes directory
- keep the current ranking/query pipeline unchanged after indexing so the slice stays vertical but bounded
- persist enough metadata to reuse parsed notes safely: relative path, parsed tags/body, and source signature
- expose CLI flags for index-file selection and forced rebuild

## Follow-up ideas
- move from whole-note cache entries to term/posting structures for larger vaults
- index headings separately for better ranking and navigation
- add timing stats to demonstrate cache-hit improvements in README screenshots or benchmarks
