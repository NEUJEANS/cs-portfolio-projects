# crdt-orset-lab research — 2026-04-18 — HTML gallery packaging

## Goal
Add a tiny browser-friendly OR-Set artifact gallery that links the Markdown, Mermaid, SVG, and JSON outputs without making the sample bundle fragile.

## Brief reference checked
- MDN `<object>` element reference: confirms HTML can embed an external resource via `data` + `type` and use fallback content while the embedded resource loads.

## Decision
Use an **inline SVG preview plus relative companion links** instead of relying on `<object>` for the main preview.

## Why
- the gallery is meant to work reliably as a committed `docs/artifacts/.../index.html` file opened directly from GitHub Pages or a local `file://` path
- inline SVG avoids a blank preview if a browser or static host treats the embedded file path awkwardly
- separate relative links still preserve the reusable artifact bundle (`.md`, `.mmd`, `.svg`, `.json`) for README links, downloads, and diffs

## Implementation note
The gallery should therefore:
1. render the same timeline story inline for immediate viewing
2. link the exported Markdown / Mermaid / SVG / JSON files next to it
3. keep all links relative to the HTML file so the committed bundle stays movable/resumable
