# Refresh notes: heading scoring and backlink extraction in Python

Date: 2026-04-14
Project: `projects/markdown-notes-search`

## Refreshed ideas
- Markdown heading extraction can stay simple for a CLI slice: scan lines, keep those beginning with `#`, and normalize later only if needed.
- Regex is enough for controlled link extraction when the goal is note-to-note references rather than full Markdown rendering.
- When cache schemas evolve, explicit versioning is cleaner than trying to partially upgrade unknown older payloads in place.
- Snippet selection should prefer the most informative context first; for note search that often means section titles before body excerpts.

## Self-test questions
1. Why prefer heading snippets first?
   - Because section titles compress intent better than arbitrary body substrings.
2. Why version the cache?
   - To avoid reusing old cached entries that lack newly indexed metadata such as headings or backlinks.
3. Why support both wikilinks and Markdown links?
   - Because note collections commonly mix both styles, especially when shared between Obsidian-like tools and plain Markdown workflows.
