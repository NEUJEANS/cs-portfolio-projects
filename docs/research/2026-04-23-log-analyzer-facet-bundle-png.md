# Research — 2026-04-23 — log-analyzer facet gallery/detail PNG exports

## Goal
Add raster exports for the facet-ranking gallery and detail-bundle workflows so the repo can ship screenshot-ready overview artifacts and reviewer handoff packets without manual browser capture.

## Quick findings
- Chrome Headless officially supports `--screenshot` together with `--window-size`, which means the existing self-contained HTML gallery and bundle pages can be rasterized without introducing extra Python imaging dependencies.
- Reusing the existing HTML pages as the screenshot source keeps the PNG outputs aligned with the committed browser artifacts and avoids maintaining a second rendering path just for screenshots.
- The previous card-PNG slice already proved the local Chrome capture path, so this follow-up should stay focused on wiring bundle/gallery outputs, manifest links, and deterministic packet contents.

## Sources checked
- Chrome for Developers — Headless mode: https://developer.chrome.com/docs/chromium/headless

## Slice decision
Implement `--facet-ranking-gallery-png` plus `--facet-ranking-detail-bundle-pngs`, then regenerate committed sample artifacts so both the gallery overview and the per-slice bundle packet can ship HTML and PNG together.

## Why this slice
The gallery/detail HTML outputs are already portfolio-friendly, but recruiters, mentors, and slide decks often want one immediately pasteable image. Adding first-class PNG exports closes that last-mile presentation gap while preserving the richer HTML packet for deeper review.
