# markdown-notes-search persistent index refresh

Date: 2026-04-14
Project: `markdown-notes-search`

## Refresh topics
- JSON serialization/deserialization for small durable cache files
- `Path.stat()` fields that are cheap and useful for cache invalidation (`st_mtime_ns`, `st_size`)
- relative-vs-absolute path handling so cache files can live inside the searched notes directory

## Quick self-test
1. If a note's `mtime_ns` and `size` are unchanged, it is safe for this tool to reuse the cached parsed note.
2. If a note changes or is newly added, rebuild only that note's cached record.
3. If a note is deleted, drop its cached entry on the next index refresh.
4. If cache contents look suspicious, provide a full rebuild flag instead of silently trusting stale data.

## Result
Proceed with a JSON-backed cache keyed by relative note path, validated by `(mtime_ns, size)`, plus a rebuild option.
