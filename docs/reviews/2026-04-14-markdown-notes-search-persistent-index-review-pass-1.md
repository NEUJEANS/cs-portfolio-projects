# Review pass 1 — markdown-notes-search persistent index

Date: 2026-04-14

## Focus
Manual code review of persistent cache read/write flow.

## Issue found
- `load_index_cache()` would crash on malformed JSON instead of treating the cache as disposable state.

## Fix
- wrapped cache JSON parsing in `try/except json.JSONDecodeError` and fall back to an empty cache.

## Result
- corrupted cache files no longer block search runs; the next save rewrites a healthy index.
