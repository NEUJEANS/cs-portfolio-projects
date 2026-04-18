# Research — 2026-04-18 — page-replacement gallery slice

## Why this slice next
The project already exported single-study Markdown / SVG / CSV artifacts, but a portfolio reviewer still had to open each workload separately. The next strongest slice is a bundled HTML gallery that lets someone browse multiple page-fault-vs-frame studies in one place and download the per-workload companions from the same page.

## Brief external refresh
- reviewed MDN guidance around semantic `<figure>` / `<figcaption>` usage so each chart card has a visible caption and accessible grouping
- rechecked inline SVG accessibility guidance: keep a `<title>` and `<desc>` for each chart and avoid duplicate IDs when multiple SVGs appear on the same page
- kept the gallery self-contained so the committed HTML works directly from GitHub Pages-style static hosting or local file previews

## Implementation goal
Ship one vertical slice that:
1. generates a multi-workload HTML gallery from the built-in presets,
2. writes Markdown / SVG / CSV / JSON companion artifacts per workload, and
3. keeps the bundle resumable so future slices can add heavier trace sets or new policies without redesigning the docs surface.
