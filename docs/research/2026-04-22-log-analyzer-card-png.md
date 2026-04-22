# Research — 2026-04-22 — log-analyzer card PNG exports

## Goal
Add raster export helpers for the existing trend-card and facet-comparison card workflows so the portfolio can ship slide-ready/chat-friendly PNG artifacts without manual screenshots.

## Quick findings
- Chrome Headless officially supports `--screenshot`, `--window-size`, and `--virtual-time-budget`, which is enough to rasterize the analyzer's self-contained HTML card pages without adding Python imaging dependencies.
- The same docs note that headless Chrome can capture pages directly from local file URLs, which fits the repo's existing static HTML artifact pattern.
- Python's `tempfile` helpers are the simplest standard-library path for ephemeral HTML files when the user requests a PNG without also requesting a persisted HTML export.

## Sources checked
- Chrome for Developers — Headless mode: https://developer.chrome.com/docs/chromium/headless
- Python docs — `tempfile`: https://docs.python.org/3/library/tempfile.html

## Slice decision
Implement standalone `--time-bucket-card-png` and `--facet-compare-card-png` exports backed by headless Chrome, plus shared sizing/capture controls and committed sample PNG artifacts.

## Why this slice
It closes a real presentation gap: SVG/HTML are great for the repo, but recruiters, slide decks, chat uploads, and status notes often want a single PNG they can paste immediately.
