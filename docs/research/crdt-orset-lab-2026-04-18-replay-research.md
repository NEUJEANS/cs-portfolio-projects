# crdt-orset-lab research — 2026-04-18 — replay/accessibility slice

## Goal
Ship a browser-friendly replay page for the OR-Set artifact bundle without turning the page into a heavyweight app, while still giving assistive technology users a useful announcement when the current replay step changes.

## Brief reference checked
- MDN `aria-live` reference: recommends updating a dedicated live region with a short message when dynamic page content changes, and notes related attributes such as `aria-atomic` when the full message should be announced together.

## Decision
Use a tiny generated HTML page with:
1. a range scrubber + play/pause controls for replaying the scripted OR-Set steps
2. a polite live region for step announcements
3. `aria-atomic="true"` so the current step summary is announced as one complete message instead of partial fragments

## Why
- the replay page is committed under `docs/artifacts/...`, so it should stay portable on GitHub Pages and simple local static hosting
- the slider/playback controls make the artifact feel like a demo instead of a static dump
- the live region keeps the changing state legible to screen-reader users without forcing focus jumps

## Implementation note
Keep the page generated from the same snapshot JSON/timeline data as the Markdown / SVG / anti-entropy outputs so the replay narration and the underlying CRDT facts stay in sync.
