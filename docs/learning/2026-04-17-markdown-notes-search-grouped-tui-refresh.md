# Markdown Notes Search Grouped TUI Refresh

Date: 2026-04-17
Project: `markdown-notes-search`

## Quick refresh
- Treat grouped TUI rows as a presentation layer on top of the existing section-scoped results instead of changing the core search/export model.
- Preserve the best-ranked result order by grouping around the first visible section hit for each dense note cluster.
- Keep grouped follow-up actions reversible: when a grouped row is marked, opened, or exported, expand it back into the original section-level results.

## Self-test
1. If a note produces two section-scoped hits in TUI mode, what should grouped view show?
   - One grouped note-level row representing both section hits.
2. What should `Enter` or export do on that grouped row?
   - Expand the grouped row back into both underlying section-scoped results.
3. What should happen to a lone section hit from another note when grouped view is enabled?
   - It should remain a normal section result instead of being forced into a synthetic group.
