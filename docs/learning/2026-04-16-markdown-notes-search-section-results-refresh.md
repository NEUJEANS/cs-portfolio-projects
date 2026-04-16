# Markdown Notes Search Section Results Refresh

Date: 2026-04-16
Project: `markdown-notes-search`

## Quick refresh
- Keep note-level filtering first, then expand into section-scoped results so boolean/path/tag matching still works as the coarse retrieval stage.
- Reuse line-aware editor commands from `section_match` metadata instead of inventing a second open-path model.
- Prefer a stable display-path helper (`path#anchor` for section hits, plain path otherwise) so text output, JSON output, exports, and TUI summaries stay aligned.

## Self-test
1. If one note has two matching sections, should the CLI return one note hit or two section hits in section mode?
   - Two section hits.
2. What metadata should stay attached to a section-scoped hit for editor integration?
   - `section_match.path`, `section_match.path_with_anchor`, and `section_match.line_number`.
3. What is the safe fallback when a note matches only filename/tag metadata and no concrete section matches?
   - Keep the note-level result instead of dropping it.
