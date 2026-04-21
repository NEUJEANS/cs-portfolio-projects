# Two-phase commit lab learning + self-test — 2026-04-21 — blocked timeline gallery slice

## Quick refresh
- A blocked-case gallery should complement the incident dashboard instead of restating it. The dashboard is triage-first; the gallery is visual-first.
- Reusing committed PNG covers keeps the page lightweight and makes the artifact deterministic for GitHub browsing.
- Clicking a cover should prefer the richer walkthrough artifact, usually timeline HTML, instead of trapping the reader on the raw PNG asset.

## Self-test
1. **Why generate a separate gallery when the incident dashboard already exists?**  
   Because the gallery is optimized for quick visual scanning of the blocked cases, while the dashboard is optimized for response classification and incident facts.
2. **Why keep the gallery static and self-contained?**  
   Because static committed artifacts are easy to browse on GitHub Pages, easy to regenerate in CI or cron, and do not add runtime dependencies.
3. **Why make the preview click-through open the full timeline walkthrough first?**  
   Because the PNG is just the cover; the HTML or SVG artifact carries the full explanation and is the better next step for a recruiter or interviewer.
