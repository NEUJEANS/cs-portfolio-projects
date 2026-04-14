# 2026-04-14 Markdown Notes Search Upgrade Research

Goal: turn a minimal filename/tag grep into a more portfolio-worthy retrieval CLI.

Brief takeaways from web research:
- note-search CLIs commonly combine filename, tag, and full-text signals rather than treating every hit equally
- contextual snippets make search results much easier to scan than bare filenames
- recursive indexing matters because real note collections are usually nested by topic or date
- simple metadata support (for example `tags:` in front matter) adds useful structure without introducing heavy dependencies

Applied decisions for this slice:
1. add recursive Markdown discovery with stable relative paths
2. merge inline hashtag tags with simple front matter tags
3. rank results so exact filename/tag matches beat weak body-only matches
4. include snippets and JSON output so the tool works for both demos and scripting
