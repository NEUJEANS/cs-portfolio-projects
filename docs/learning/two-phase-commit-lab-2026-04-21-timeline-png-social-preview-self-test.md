# Two-phase commit lab learning + self-test — 2026-04-21 — timeline PNG/social-preview slice

## Quick refresh
- GitHub social preview images look best around `1280x640`, so a compact dedicated cover is more useful than a raw screenshot of the full tall timeline page.
- Headless Chrome is a practical way to turn self-contained HTML into deterministic PNG artifacts without adding extra Python image dependencies.
- The social-preview PNG should summarize the incident, not replace the full SVG/HTML timeline artifact.

## Self-test
1. **Why not just screenshot the full timeline HTML page at a tiny height?**  
   Because the long-form artifact is intentionally tall and dense, so a compact preview layout keeps the important incident story legible.
2. **Why keep the SVG and HTML artifacts after adding PNG?**  
   Because the PNG is a cover asset, while the SVG/HTML keep the full step-by-step detail and accessibility-friendly browsing.
3. **What should the default PNG size optimize for first?**  
   Reuse in GitHub/social contexts, so the initial default should track the `1280x640` style guidance.
