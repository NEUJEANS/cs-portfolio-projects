# Research — 2026-04-23 — log-analyzer facet gallery/detail scorecards

## Goal
Add quick-read summary tiles to the facet gallery and detail-bundle index so overview screenshots explain the busiest slices before a reviewer opens the full ranking tables.

## Quick findings
- MDN's CSS Grid guidance is a good fit for small responsive summary tiles because the scorecards can stay readable across gallery cards, bundle cards, and PNG captures without hard-coded columns.
- MDN's `<dl>` accessibility notes are a reminder to keep compact label/value groupings simple and semantic; for this repo, lightweight card blocks with clear labels are safer than trying to overload table headers for the overview layer.
- The best implementation path is to derive scorecards from the existing top-path/referrer/user-agent/IP rows rather than creating a second analysis pass, so gallery tables, bundle manifests, and screenshots cannot drift.

## Sources checked
- MDN — CSS Grid Layout: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout
- MDN — `<dl>` element reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dl

## Slice decision
Reuse the existing facet-ranking data to surface `At a glance` scorecards in the gallery cards and detail-bundle index/manifest, then regenerate the committed sample artifacts.

## Why this slice
The gallery and bundle already had the right data, but overview screenshots still forced reviewers to read full tables first. Small derived scorecards improve first-glance storytelling without adding new CLI flags or a parallel rendering pipeline.
