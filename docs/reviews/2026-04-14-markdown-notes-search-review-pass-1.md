# 2026-04-14 Markdown Notes Search Review Pass 1

Focus: code audit for ranking and parsing logic.

Findings:
- Removed an unused regex constant left behind from an earlier draft.
- Hardened `search_notes()` to return no results for blank queries and reject non-positive limits.
- Confirmed result sorting is deterministic by score and relative path.

Fixes applied:
- deleted dead code
- added validation for empty queries and invalid limits
- added regression coverage for those cases
