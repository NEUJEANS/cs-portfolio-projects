# 2026-04-14 Markdown Notes Search Review Pass 2

Focus: CLI smoke test with nested notes and front matter.

Finding:
- Snippets initially included raw front matter lines, which made output noisy and less demo-friendly.

Fix applied:
- strip front matter from the indexed/searchable body while still preserving front matter tags as metadata
- added a regression test to ensure snippets exclude `tags:` metadata lines

Validation:
- ran project unit tests
- ran a recursive CLI smoke test against a temporary nested note tree
