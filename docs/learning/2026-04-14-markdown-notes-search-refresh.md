# 2026-04-14 Markdown Notes Search Refresh

Quick refresh before coding:
- `Path.glob('**/*.md')` is enough for recursive note discovery without extra dependencies
- regex word-boundary style checks are useful to score exact-token hits above loose substring hits
- snippets should normalize whitespace and clamp context windows so CLI output stays readable
- JSON output should include only serializable search fields, not the full note body

Self-test prompts answered before implementation:
- How do I keep nested results stable? Use relative paths from the searched root.
- How should front matter stay lightweight? Support a simple `tags:` line instead of full YAML parsing.
- What should rank highest? Exact filename and tag matches, then repeated body hits.
