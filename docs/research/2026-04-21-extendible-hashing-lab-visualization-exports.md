# Extendible hashing visualization-exports research — 2026-04-21

## Sources checked
- MDN, `ARIA: aria-labelledby attribute`
- MDN, `<title> — the SVG accessible name element`
- MDN, `<desc> - SVG`

## Notes that mattered for this slice
- `aria-labelledby` is meant to reference other elements in the DOM by ID, so generated SVG should emit concrete IDs instead of relying on anonymous `<title>` / `<desc>` nodes.
- SVG `<title>` provides the short accessible name and also doubles as a browser tooltip for the element it annotates.
- SVG `<desc>` provides the longer-form accessible description; MDN explicitly notes that it can be referenced by ID when wiring ARIA descriptions.
- Because the SVG cards intentionally truncate long directory/bucket labels for layout stability, nested `<title>` elements on grouped rows are the simplest standards-friendly way to preserve the full text without bloating the visual layout.

## Takeaway for implementation
Give each exported SVG a stable `title`/`desc` ID pair for `aria-labelledby`, and wrap truncated step/row content in `<g><title>...</title>...</g>` so the artifact stays compact while still exposing the full story on hover and to assistive tech.
