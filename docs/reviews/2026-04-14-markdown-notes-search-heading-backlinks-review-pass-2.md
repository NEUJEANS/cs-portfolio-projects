# Review pass 2 — CLI smoke test

Date: 2026-04-14
Project: `markdown-notes-search`

## What I checked
- temporary note vault with a heading match and cross-note links
- JSON output shape for `headings` and `backlinks`
- plain-text output with `--show-backlinks`

## Commands used
- `python3 notes_search.py <tmpdir> 'distributed systems' --json`
- `python3 notes_search.py <tmpdir> hub --show-backlinks`

## Findings
- heading-first JSON snippet works as intended
- backlink arrays are present in JSON output
- plain-text backlink display is opt-in and does not clutter default output
- no additional issues found in this pass
