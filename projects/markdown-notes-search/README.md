# markdown-notes-search

## Overview
Search Markdown notes by filename, inline tags, YAML-style front matter tags, and full-text matches. Results are ranked so stronger matches surface first, and each hit includes a contextual snippet for quick scanning. The CLI also supports quoted phrase queries, boolean filtering, and an optional persistent index file for larger note vaults.

## Why it is portfolio-worthy
- demonstrates text indexing, lightweight information retrieval, query parsing, and CLI product design
- supports recursive vault-style note collections rather than a single flat folder
- adds a persistent JSON-backed index cache to avoid reparsing unchanged notes on repeated searches
- balances human-readable output with JSON output for scripting and automation
- includes automated tests for ranking, metadata parsing, cache refresh behavior, recursion, boolean logic, and CLI behavior

## Stack
- Python
- standard library only (`argparse`, `json`, `pathlib`, `re`)

## Features
- index Markdown notes from a directory or nested note tree
- extract inline hashtag tags like `#graphs`
- merge tags declared in simple front matter such as `tags: [graphs, cli]`
- rank results using filename, path, tag, and body-match signals
- show contextual snippets around the first hit
- support quoted phrase queries like `"systems design"`
- support boolean queries with `AND`, `OR`, `NOT`, and parentheses
- treat adjacent operands as implicit `AND` for ergonomic searching
- optionally persist parsed note metadata in `.notes_search_index.json`
- automatically refresh cached entries for changed files and drop deleted files from the index
- emit plain text or JSON output
- limit output for focused workflows

## Usage
```bash
python3 notes_search.py notes graphs
python3 notes_search.py notes systems --recursive --limit 5
python3 notes_search.py notes 'distributed AND systems' --recursive
python3 notes_search.py notes '(graph OR tree) AND NOT archived' --recursive
python3 notes_search.py notes '"systems design" OR architecture' --recursive --json
python3 notes_search.py notes graphs --recursive --index-file .notes_search_index.json
python3 notes_search.py notes graphs --recursive --index-file .notes_search_index.json --rebuild-index
```

### Example output
```text
school/algorithms/graphs.md (score=171) [#cli #graphs]
  …Study #graphs and shortest path algorithms for the systems interview prep…
```

## Query notes
- precedence is `NOT` > `AND` > `OR`
- parentheses can override default grouping
- quoted text is treated as an exact multi-word phrase
- adjacent operands are treated as implicit `AND`

## Persistent index notes
- pass `--index-file .notes_search_index.json` to enable a reusable JSON cache in the notes directory
- cached entries are reused only when file size and nanosecond mtime still match
- changed files are reparsed automatically and deleted files are removed from the index on the next run
- pass `--rebuild-index` when you want to discard prior cache contents and regenerate from scratch

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- add heading-aware ranking and backlink-aware navigation
- add a TUI browsing mode with preview panes
- support richer incremental posting-list structures instead of whole-note JSON cache entries
