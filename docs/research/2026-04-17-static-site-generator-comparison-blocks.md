# 2026-04-17 static-site-generator comparison blocks research

## Brief takeaways
- Markdown Guide’s extended-syntax overview reinforces that richer authoring patterns usually come from lightweight processor extensions rather than core Markdown, so a small custom container syntax is reasonable for a hand-rolled renderer.
- MDN’s CSS Grid basics remain a good fit for this slice because the layout only needs a simple responsive two-column arrangement that can collapse to one column on narrow screens.
- For portfolio storytelling, the most useful structure is not a generic multi-column container but a focused before/after/delta narrative that explains baseline state, improved state, and measurable impact.

## Slice decision
- add a `::: comparison` fenced container with named `::before::`, `::after::`, and optional `::delta::` sections
- keep authoring syntax readable in raw Markdown without introducing external parser dependencies
- render the panels with a small responsive grid plus a separately emphasized delta stack for benchmark or outcome notes
