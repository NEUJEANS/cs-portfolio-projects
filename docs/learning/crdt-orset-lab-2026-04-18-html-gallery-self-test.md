# crdt-orset-lab learning/self-test — 2026-04-18 — HTML gallery slice

## Refresh
No large HTML refresh was needed; this slice only needed a quick reminder that a static artifact page should prefer simple relative links and self-contained previews over any JS-heavy viewer.

## Self-test checklist
- generated `docs/artifacts/crdt-orset-lab/index.html` from the CLI, not by hand
- confirmed the HTML includes relative links to `sample-ops-timeline.md`, `sample-ops-timeline.mmd`, `sample-ops-timeline.svg`, and `sample-ops-snapshot.json`
- confirmed the page inlines the SVG preview so the artifact story is visible even before clicking companion files
- confirmed the raw JSON snapshot is emitted as a committed artifact, so the gallery is not only presentation polish

## Takeaway
For portfolio artifacts, a tiny static HTML index is often enough to make a project feel navigable. The key is to keep it generated from the same source snapshot as the Markdown/SVG files so the story and the raw data cannot drift apart silently.
