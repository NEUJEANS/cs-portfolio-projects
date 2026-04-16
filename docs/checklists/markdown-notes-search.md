# Markdown Notes Search Checklist

Status: vertical slice 9 complete
Last updated: 2026-04-16

## Vertical slice 1
- [x] identify markdown-notes-search as one of the weakest portfolio projects due to minimal search quality and docs
- [x] do brief research on note-search UX and ranking ideas
- [x] do short Python text-processing refresh and self-test
- [x] extend checklist and project docs for a stronger retrieval-focused slice
- [x] implement recursive indexing for nested note trees
- [x] add front matter tag parsing and inline-tag merging
- [x] add ranked results with snippets and JSON output
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 2
- [x] do brief research on lightweight boolean retrieval patterns
- [x] do short parser/precedence refresh and self-test
- [x] update checklist and docs for boolean query support
- [x] implement phrase search with quoted terms
- [x] implement boolean `AND` / `OR` / `NOT` queries with parentheses
- [x] keep implicit `AND` between adjacent operands for ergonomic CLI use
- [x] add automated coverage for phrase, precedence, grouping, and invalid queries
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 3 — persistent index cache
- [x] identify markdown-notes-search as still worth another slice because repeated searches reparsed every note from scratch
- [x] do brief research on persistent index cache design for simple note search CLIs
- [x] do short Python JSON/file-signature refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add optional persistent JSON index support for repeated searches
- [x] refresh changed files and drop deleted files automatically from the cache
- [x] add CLI flags for index path selection and full rebuilds
- [x] expand automated coverage for cache creation, refresh, deletion handling, and CLI index generation
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 4 — heading-aware ranking and backlink navigation
- [x] identify markdown-notes-search as still worth another slice because ranking ignored section headings and cross-note note graph context
- [x] do brief implementation research on heading-weighted note ranking and markdown link/backlink extraction patterns
- [x] do short Python regex/link-normalization refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add heading extraction and heading-aware scoring/snippet selection
- [x] add wiki-link and markdown-link parsing with backlink graph enrichment across indexed notes
- [x] expose backlink data in JSON output and optional plain-text output
- [x] expand automated coverage for heading ranking, backlink indexing, and cache version upgrades
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 5 — section-scoped retrieval and anchor navigation
- [x] identify markdown-notes-search as still worth another slice because results could rank a note correctly without showing the exact matching section to jump to
- [x] do short heading-anchor and section-index refresh with self-test
- [x] update checklist/docs so the slice is resumable
- [x] add section extraction with deterministic heading anchors and duplicate-heading suffix handling
- [x] expose best matching `path#anchor` section navigation metadata in search results and JSON output
- [x] add optional plain-text section display for terminal workflows
- [x] expand automated coverage for unique anchors, section-match ranking, and CLI JSON output
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 6 — editor jump commands
- [x] identify markdown-notes-search as still worth another slice because section anchors were exposed but terminal workflows still lacked a practical editor jump action
- [x] do brief research on CLI editor command patterns and line-aware jump conventions
- [x] do short Python `shlex` / subprocess refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add section line metadata so search results can point editors at the matching heading
- [x] add generated editor open commands for common editors plus CLI flags to print or launch them
- [x] expose editor commands and line metadata in JSON output for automation
- [x] expand automated coverage for line metadata, editor command generation, and CLI JSON output
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 7 — TUI browsing mode with preview panes
- [x] confirm markdown-notes-search still had a clear unfinished item: interactive browsing existed only as a future improvement
- [x] do brief research on Python curses layout basics for list/detail terminal UIs
- [x] do short Python text-wrapping and keyboard-loop refresh/self-test
- [x] update checklist/docs so the slice is resumable
- [x] add `--tui` mode with a left-side ranked result list and right-side preview pane
- [x] keep plain-text, JSON, and editor-open workflows backward compatible
- [x] add automated coverage for TUI-friendly result summarization and preview rendering helpers
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up


## Vertical slice 8 — multi-result TUI actions and export bundles
- [x] identify markdown-notes-search as still worth another slice because the TUI could browse one result at a time but could not batch follow-up actions
- [x] skip external web research because the next slice was already scoped clearly in the local checklist and README
- [x] do short Python curses selection-state and export-format refresh by sketching the key handling and export payload shape before editing
- [x] update checklist/docs so the slice is resumable
- [x] add TUI multi-result marking with batch open support
- [x] add Markdown/JSON export bundles for current search results with reusable editor commands
- [x] wire TUI export to `--export-results` so interactive sessions can save the marked subset
- [x] expand automated coverage for export helpers, selection helpers, and CLI export output
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 9 — section-scoped result expansion
- [x] identify markdown-notes-search as still worth another slice because a single best section per note limited multi-anchor follow-up workflows
- [x] skip external web research because the existing checklist, README, and code structure already scoped the next section-results slice clearly
- [x] do short Python result-shaping and line-aware editor-command refresh with a small self-test note before editing
- [x] update checklist/docs so the slice is resumable
- [x] add `--section-results` so ranked note hits can expand into multiple section-scoped results from the same note
- [x] preserve section-aware editor commands, JSON output, export bundles, and TUI previews for section-scoped results
- [x] expand automated coverage for section-result expansion, JSON output, and Markdown export bundles
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Next slice candidates
- [ ] richer posting-list style incremental index rather than storing full note bodies in cache
- [x] multi-result TUI actions such as bulk-open or export
- [x] section-scoped retrieval with heading anchors and open-in-editor actions for multiple selected hits
- [ ] collapse/group dense section-result clusters from the same note in TUI mode
