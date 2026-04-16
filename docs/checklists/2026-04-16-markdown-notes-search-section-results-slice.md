# Markdown Notes Search Section Results Slice Checklist

Date: 2026-04-16
Project: `markdown-notes-search`

## Goal
Add a true section-scoped result mode so multiple matching anchors from the same note can be reviewed, exported, and opened independently.

## Checklist
- [x] confirm this is the next unfinished/weakest markdown-notes-search follow-up item
- [x] skip external web research because the local checklist and README already scoped the slice clearly
- [x] do a short Python refresh/self-test for result shaping and line-aware editor flows
- [x] update the main project checklist and README before/alongside code changes
- [x] implement `--section-results` expansion for multiple matching sections in one note
- [x] keep plain-text output, JSON output, export bundles, and TUI flows compatible with section results
- [x] add automated tests for section-result ranking/expansion and exports
- [x] run the project test suite
- [x] review pass 1 and fix findings
- [x] review pass 2 and fix findings
- [x] review pass 3 and fix findings
- [x] run a secret scan before push
- [x] commit, push, and add wrap-up

## Notes
- Result paths should stay editor-friendly while also surfacing `path#anchor` clearly in text and JSON.
- If a query matches only note-level metadata and not a concrete section, the result can stay note-scoped as a fallback.
