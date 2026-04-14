# Review pass 1 — automated test audit

Date: 2026-04-14
Project: `markdown-notes-search`

## What I checked
- full unit test suite with `python3 -m unittest discover -s . -p 'test_*.py'`

## Issues found
1. heading matches were returning a body snippet instead of a heading-first snippet
2. backlink test assumption was too strict because exact filename matches should still outrank backlink-only matches
3. cache refresh test was flaky when file mtimes did not advance fast enough on rewrite

## Fixes applied
- changed snippet selection to prefer heading snippets before body excerpts
- updated backlink coverage to assert backlink navigation presence without breaking exact-match ranking
- stabilized the cache-refresh test with a tiny delay and explicit `os.utime()` refresh

## Result
- test suite passes after fixes
