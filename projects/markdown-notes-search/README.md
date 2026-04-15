# markdown-notes-search

## Overview
Search Markdown notes by filename, inline tags, YAML-style front matter tags, headings, backlinks, and full-text matches. Results are ranked so stronger matches surface first, and each hit includes a contextual snippet for quick scanning. The CLI also supports quoted phrase queries, boolean filtering, backlink-aware navigation, section-level anchor hints, generated editor jump commands, and an optional persistent index file for larger note vaults.

## Why it is portfolio-worthy
- demonstrates text indexing, lightweight information retrieval, query parsing, and CLI product design
- supports recursive vault-style note collections rather than a single flat folder
- adds a persistent JSON-backed index cache to avoid reparsing unchanged notes on repeated searches
- boosts notes whose headings directly match the query and surfaces heading-first snippets for faster scanning
- extracts wiki-style and Markdown links to build backlink-aware navigation across note graphs
- balances human-readable output with JSON output for scripting and automation
- includes automated tests for ranking, metadata parsing, backlink enrichment, cache refresh behavior, recursion, boolean logic, and CLI behavior

## Stack
- Python
- standard library only (`argparse`, `json`, `pathlib`, `re`)

## Features
- index Markdown notes from a directory or nested note tree
- extract inline hashtag tags like `#graphs`
- merge tags declared in simple front matter such as `tags: [graphs, cli]`
- rank results using filename, path, tag, heading, backlink, and body-match signals
- show contextual snippets around the first hit, preferring heading snippets when the query lands in a section title
- support quoted phrase queries like `"systems design"`
- support boolean queries with `AND`, `OR`, `NOT`, and parentheses
- treat adjacent operands as implicit `AND` for ergonomic searching
- optionally persist parsed note metadata in `.notes_search_index.json`
- automatically refresh cached entries for changed files and drop deleted files from the index
- parse `[[wikilinks]]` and standard Markdown links to populate backlinks
- emit plain text or JSON output, with optional backlink and section-anchor display in the terminal
- include best-match `path#anchor` metadata, section line numbers, and generated editor commands so other tools or editors can jump straight to the relevant heading
- limit output for focused workflows

## Usage
```bash
python3 notes_search.py notes graphs
python3 notes_search.py notes systems --recursive --limit 5
python3 notes_search.py notes 'distributed AND systems' --recursive
python3 notes_search.py notes '(graph OR tree) AND NOT archived' --recursive
python3 notes_search.py notes '"systems design" OR architecture' --recursive --json
python3 notes_search.py notes graphs --recursive --index-file .notes_search_index.json
python3 notes_search.py notes graphs --recursive --show-backlinks
python3 notes_search.py notes "phi accrual" --recursive --show-sections
python3 notes_search.py notes "phi accrual" --recursive --show-sections --show-open-command --editor "code --reuse-window"
python3 notes_search.py notes graphs --recursive --index-file .notes_search_index.json --rebuild-index
```

### Example output
```text
school/systems/distributed.md (score=166) [#distributed #systems]
  Failure Detection (#failure-detection): Heartbeat timeout and phi accrual notes…
  section: school/systems/distributed.md#failure-detection:7
```

## Query notes
- precedence is `NOT` > `AND` > `OR`
- parentheses can override default grouping
- quoted text is treated as an exact multi-word phrase
- adjacent operands are treated as implicit `AND`

## Backlink notes
- wikilinks like `[[systems/design]]` and Markdown links like `[design](systems/design.md)` are normalized into note-to-note graph edges
- inbound references become `backlinks` on each result and can be shown in text mode with `--show-backlinks`
- JSON output includes `headings`, `sections`, `section_match`, and `backlinks` so other tools can build richer note browsers on top

## Persistent index notes
- pass `--index-file .notes_search_index.json` to enable a reusable JSON cache in the notes directory
- cached entries are reused only when file size and nanosecond mtime still match
- changed files are reparsed automatically and deleted files are removed from the index on the next run
- the cache format is versioned so new metadata fields can be rolled out safely
- pass `--rebuild-index` when you want to discard prior cache contents and regenerate from scratch

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Editor jump notes
- pass `--show-open-command` to print a ready-to-run editor command beside each text result
- use `--editor "code --reuse-window"` (or `vim`, `nvim`, `nano`, `subl`, etc.) to generate editor-specific jump commands
- pass `--open-result` to launch the top result immediately in the configured editor
- JSON output includes `section_match.line_number` and `open_command` for shell scripts or TUI wrappers

## Future Improvements
- add a TUI browsing mode with preview panes
- support richer incremental posting-list structures instead of whole-note JSON cache entries
- add multi-result interactive selection instead of opening only the top hit
