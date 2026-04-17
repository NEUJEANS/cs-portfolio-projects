# Static Site Generator — date archive slice research

Date: 2026-04-17

## Goal
Add lightweight, portfolio-friendly archive browsing for dated pages without turning the project into a full CMS.

## Brief research takeaways
Based on quick archive/timeline UX research, the most useful patterns for a small static portfolio are:

- keep archive discovery obvious from the main navigation
- show entries in reverse chronological order so the newest work is easiest to find
- group long histories by year/month to stay scannable instead of dumping one giant list
- use concise cards/lists with title + short description rather than full post bodies
- provide stable date-based URLs for archive pages
- allow dated pages to opt out when they are drafts or private notes

## Slice decision
Implement a generated archive index plus yearly archive pages:

- `archives/index.html`
- `archives/<year>/index.html`

Each yearly page should:

- group entries by month
- keep months in reverse chronological order
- provide quick jump links to each month section
- link back to the main archive index

## Scope guardrails
- no pagination yet
- no monthly standalone pages yet
- no dependency-heavy date library
- no change to RSS behavior beyond reusing existing `date` metadata

## Follow-up ideas
- monthly landing pages for larger portfolios
- featured entry excerpts or thumbnails in archive cards
- optional archive-specific layout hooks in front matter or `_site.json`
