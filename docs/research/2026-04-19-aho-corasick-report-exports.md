# 2026-04-19 Aho-Corasick Report Export Research

## Goal
Add portfolio-friendly Markdown/HTML report exports without breaking the existing CLI automation story.

## Brief references checked
- Python `html.escape(...)` docs: escape `&`, `<`, `>`, and quoted attribute characters before rendering match excerpts into HTML.
- Python `pathlib.Path` docs: use `Path(...).parent.mkdir(parents=True, exist_ok=True)` plus `write_text(...)` for straightforward deterministic artifact writes.

## Notes used for this slice
- report files should be side effects only; stdout must still be usable for normal text output or JSON pipelines
- the HTML view only needs static inline CSS and escaped text snippets to be screenshot/demo friendly
- committed sample artifacts should show real hits, not an empty report, so the fixture command must use the checked-in sample keyword file
