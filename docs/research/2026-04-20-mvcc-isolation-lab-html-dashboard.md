# MVCC isolation lab HTML dashboard note — 2026-04-20

## Research decision
No extra external web research was needed for this slice.

## Why
- the feature is a static presentation/export layer on top of already-tested local compare results, not a new database-isolation semantic
- the dashboard is plain HTML/CSS with relative links to already-generated Markdown and SVG artifacts, so the design constraints are repo-local and GitHub Pages friendly
- the main risk is clarity rather than standards ambiguity: making it obvious which modes stayed invariant-safe, which modes aborted, and why

## Design takeaway
- keep the export dependency-free and deterministic so committed artifacts diff cleanly
- link the Markdown comparison and per-isolation timelines instead of duplicating the full raw trace in the page
- surface scenario footprint and abort-cause summaries near the top so a recruiter can understand the story in seconds
