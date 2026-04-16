# 2026-04-16 distributed snapshot PNG assets research

## Goal
Finish the next distributed-snapshot presentation slice by producing committed PNG walkthrough assets for tools that still mangle or reject SVG embeds.

## Why this is the right next slice
- The lab already has deterministic Markdown walkthrough output and committed SVG artifacts.
- The remaining portability gap is slide software and portfolio builders that prefer raster images.
- PNG export should build on the existing SVG renderer so the visual contract stays single-sourced and diffable.

## Constraints
- avoid adding a heavyweight Python image dependency just to rasterize a handful of diagram assets
- keep the workflow resumable from the CLI so docs/artifacts can be regenerated in one command
- preserve exact diagram sizing so screenshots do not pick up browser chrome or extra whitespace

## Chosen implementation direction
- keep SVG as the canonical generated asset format
- detect a local headless browser (`google-chrome`, `chromium`, or `chromium-browser`) only when PNG export is explicitly requested
- render PNGs by opening the generated SVG in headless browser mode and taking a screenshot at the SVG's own width/height
- link PNG assets from the walkthrough without replacing the existing SVG embeds, so vector and raster assets can coexist cleanly
