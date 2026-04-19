# 2026-04-19 Aho-Corasick Report Export Refresh

## Refresher
- The search result payload already contains everything needed for text, JSON, Markdown, and HTML views; adding reports is mostly a rendering/export problem, not a second search pass.
- File outputs should stay deterministic so repeated artifact generation does not create noisy diffs.
- A portfolio artifact is more convincing when it is generated from the checked-in fixtures and can be reproduced with one README command.

## Quick self-test
1. Why keep stdout separate from report files? So existing scripts can still consume text or JSON without scraping the report artifacts.
2. Why use escaped snippets in HTML? Because sample text can contain `<`, `>`, `&`, or quotes, and report output should never reinterpret match excerpts as markup.
3. Why commit a real sample artifact instead of only mentioning the flags? Because the repo should already contain a screenshot/demo-ready example for reviewers and recruiters.
