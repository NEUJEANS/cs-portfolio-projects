# Markdown Notes Search: heading-aware ranking and backlink navigation

Date: 2026-04-14
Project: `projects/markdown-notes-search`

## Goal
Improve the portfolio value of the notes-search CLI by making results feel more like a real note-taking/search tool instead of a plain filename/body grep.

## Brief findings
- Heading text is a strong relevance signal in note systems because headings often summarize the intent of a section more directly than the surrounding paragraph text.
- Backlinks are a useful lightweight navigation primitive: even without a full graph database, parsing note-to-note links gives enough structure to surface “referenced by” context.
- For a standard-library-only Python CLI, regex-based extraction of headings, wiki links, and Markdown links is sufficient for a clean vertical slice.
- A versioned JSON cache is safer than silently reusing stale cached records when note metadata fields evolve.

## Implementation direction chosen
- extract headings during indexing and boost ranking when the query matches a heading
- prefer heading snippets before falling back to body snippets
- parse both `[[wikilinks]]` and `[text](target.md)` links
- build backlinks after indexing by matching normalized note aliases
- expose backlink data in JSON and behind an optional plain-text flag
- bump cache format version to avoid mixing old and new indexed structures

## Risks / follow-up
- link normalization is intentionally simple and may not resolve every vault convention
- backlink search is still note-level, not section-anchor-level
- next meaningful slice could add section anchors and editor-opening actions
