# markdown-notes-search

## Overview
Search Markdown notes by filename, inline tags, YAML-style front matter tags, headings, backlinks, and full-text matches. Results are ranked so stronger matches surface first, and each hit includes a contextual snippet for quick scanning. The CLI also supports quoted phrase queries, boolean filtering, backlink-aware navigation, section-level anchor hints, generated editor jump commands, section-scoped result expansion for multi-anchor follow-up work, collapse controls for dense multi-section note clusters, a lightweight TUI browser with preview panes, export bundles for sharing follow-up reading lists, and an optional persistent index file for larger note vaults.

## Why it is portfolio-worthy
- demonstrates text indexing, lightweight information retrieval, query parsing, and CLI product design
- supports recursive vault-style note collections rather than a single flat folder
- adds a persistent JSON-backed index cache to avoid reparsing unchanged notes on repeated searches
- boosts notes whose headings directly match the query and surfaces heading-first snippets for faster scanning
- extracts wiki-style and Markdown links to build backlink-aware navigation across note graphs
- balances plain terminal output, JSON output, export bundles, and an interactive TUI for scripting plus hands-on browsing
- adds collapse controls for dense section-result clusters both inside the TUI and in plain-text/JSON/export review flows
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
- optionally expand note matches into section-scoped results so several matching anchors from the same note can be opened or exported independently
- optionally collapse multi-section hits back into one grouped entry for plain-text, JSON, or export bundles while preserving the top section as the editor jump target
- browse results in a keyboard-driven TUI with a result list on the left and rich note preview on the right
- toggle grouped note-level rows inside the TUI when section-level expansion would otherwise flood the result list from one large note
- mark multiple TUI results, open them together in an editor, and export the marked subset to Markdown or JSON
- export ranked result bundles from plain CLI mode for sharing, review, or downstream automation
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
python3 notes_search.py notes failure --recursive --section-results --show-sections --show-open-command --editor "code --reuse-window"
python3 notes_search.py notes failure --recursive --section-results --collapse-sections --show-sections
python3 notes_search.py notes graphs --recursive --index-file .notes_search_index.json --rebuild-index
python3 notes_search.py notes "phi accrual" --recursive --export-results exports/phi-accrual.md
python3 notes_search.py notes "systems" --recursive --export-results exports/systems.json --export-format json
python3 notes_search.py notes failure --recursive --section-results --export-results exports/failure-sections.md --editor "code --reuse-window"
python3 notes_search.py notes "phi accrual" --recursive --tui --editor "code --reuse-window" --export-results exports/tui-selection.md
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
- pair `--section-results` with `--show-open-command`, `--export-results`, or `--tui` when you want several matching anchors from the same note to remain separate follow-up targets
- add `--collapse-sections` when those section-level hits are too dense for plain-text, JSON, or export review; collapsed entries keep a grouped section list while the top section remains the editor/open target
- pass `--open-result` to launch the top result immediately in the configured editor
- JSON output includes `section_match.line_number`, `scope`, `path_display`, and `open_command` for shell scripts or TUI wrappers

## Section collapse notes
- pass `--collapse-sections` together with `--section-results` to bundle multi-hit notes into one review-friendly entry outside the TUI
- collapsed entries list the grouped section anchors in plain text and exported Markdown/JSON bundles without losing the strongest section jump target
- TUI mode already has its own `g` grouping toggle, so `--collapse-sections` is mainly for non-TUI output and export flows

## TUI notes
- pass `--tui` to browse matches interactively inside a terminal window
- add `--section-results` before `--tui` when you want the left pane to list individual anchors instead of one best hit per note
- use `↑` / `↓` or `j` / `k` to move through results, `PageUp` / `PageDown` for larger jumps, `Space` to mark results, `g` to toggle grouped note-level rows for dense section-result clusters, and `Enter` or `o` to open the current/marked result set in your editor
- add `--export-results path.md` (or `.json` with `--export-format json`) and press `e` inside the TUI to export the marked subset; without marks, the current result is exported
- the left pane shows ranked matches while the right pane previews tags, backlinks, scope, the best section anchor, selection state, and the current snippet
- in grouped mode, one row can represent every matching section from the same note; marking, opening, or exporting that row applies to the whole grouped cluster
- if the terminal is too small, the UI waits for a resize instead of crashing

## Future Improvements
- support richer incremental posting-list structures instead of whole-note JSON cache entries
- add tunable collapse thresholds or section-distance clustering for very large notes with dozens of near-duplicate hits
