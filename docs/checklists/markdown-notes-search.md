# Markdown Notes Search Checklist

Status: vertical slice 2 complete
Last updated: 2026-04-14

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

## Next slice candidates
- [ ] persistent inverted index for larger note vaults
- [ ] TUI browsing mode with preview panes
- [ ] heading-aware ranking and backlink-aware navigation
