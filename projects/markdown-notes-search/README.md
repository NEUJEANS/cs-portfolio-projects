# markdown-notes-search

## Overview
Search Markdown notes by filename, inline tags, YAML-style front matter tags, and full-text matches. Results are ranked so stronger matches surface first, and each hit includes a contextual snippet for quick scanning.

## Why it is portfolio-worthy
- demonstrates text indexing, lightweight information retrieval, and CLI product design
- supports recursive vault-style note collections rather than a single flat folder
- balances human-readable output with JSON output for scripting and automation
- includes automated tests for ranking, metadata parsing, recursion, and CLI behavior

## Stack
- Python
- standard library only (`argparse`, `json`, `pathlib`, `re`)

## Features
- index Markdown notes from a directory or nested note tree
- extract inline hashtag tags like `#graphs`
- merge tags declared in simple front matter such as `tags: [graphs, cli]`
- rank results using filename, path, tag, and body-match signals
- show contextual snippets around the first hit
- emit plain text or JSON output
- limit output for focused workflows

## Usage
```bash
python3 notes_search.py notes graphs
python3 notes_search.py notes systems --recursive --limit 5
python3 notes_search.py notes cli --recursive --json
```

### Example output
```text
school/algorithms/graphs.md (score=171) [#cli #graphs]
  …Study #graphs and shortest path algorithms for the systems interview prep…
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support phrase search and boolean operators
- add stemming or token normalization for stronger fuzzy matching
- optionally index headings and backlinks separately for richer ranking
