# markdown-notes-search

## Overview
Search Markdown notes by filename, inline tags, YAML-style front matter tags, and full-text matches. Results are ranked so stronger matches surface first, and each hit includes a contextual snippet for quick scanning. The CLI now also supports quoted phrase queries and boolean filtering for more realistic note-vault workflows.

## Why it is portfolio-worthy
- demonstrates text indexing, lightweight information retrieval, query parsing, and CLI product design
- supports recursive vault-style note collections rather than a single flat folder
- balances human-readable output with JSON output for scripting and automation
- includes automated tests for ranking, metadata parsing, recursion, boolean logic, and CLI behavior

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
- treat adjacent terms as implicit `AND` for ergonomic searching
- emit plain text or JSON output
- limit output for focused workflows

## Usage
```bash
python3 notes_search.py notes graphs
python3 notes_search.py notes systems --recursive --limit 5
python3 notes_search.py notes 'distributed AND systems' --recursive
python3 notes_search.py notes '(graph OR tree) AND NOT archived' --recursive
python3 notes_search.py notes '"systems design" OR architecture' --recursive --json
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

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- add a persistent inverted index for larger note vaults
- optionally index headings and backlinks separately for richer ranking
- add a TUI browsing mode with preview panes
