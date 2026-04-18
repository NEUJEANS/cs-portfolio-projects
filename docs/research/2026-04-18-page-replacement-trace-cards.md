# Research note — 2026-04-18 — page-replacement trace cards

## Question
What is the most useful next `page-replacement-lab` slice after the trace-summary command and aggregate dashboard already exist?

## Brief references checked
- existing repo-local SVG study-card and aggregate-dashboard patterns in `page_replacement_lab.py`
- the committed `compiler-phase-shift` trace-summary Markdown / JSON artifacts
- current README and checklist notes for what is still missing in the portfolio story

## Takeaways used for the implementation
- extra web research is **not** needed for this reporting-focused slice because the repo already has accessible SVG IDs, inline-card patterns, and browsable HTML dashboards to copy from
- the trace-summary command already computes the right raw metrics; the missing value is a **visual artifact layer** that turns those metrics into screenshot-ready cards
- the most useful card should show both **reuse-distance distribution** and **per-window unique-page pressure**, because those two views explain locality and phase shifts quickly in interviews
- HTML output should keep the SVG inline and pair it with tables so the card is both slide-ready and inspectable in a browser

## Implementation choice
- extend `trace-summary` with `--svg-out` and `--html-out`
- generate one slide-ready SVG card plus one browsable HTML companion from the same summary payload
- export committed compiler benchmark artifacts so the new workflow is visible in the repo immediately
