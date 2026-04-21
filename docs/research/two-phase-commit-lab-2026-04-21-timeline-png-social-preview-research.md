# Two-phase commit lab research note — 2026-04-21 — timeline PNG/social-preview slice

## Goal
Add a reusable PNG export for the blocked-case peer-termination timeline artifacts so the project has screenshot-friendly covers for README usage, GitHub social previews, and slide decks.

## Brief research summary
- GitHub's repository social preview docs recommend PNG/JPG/GIF under 1 MB and say at least `640x320`, with `1280x640` giving the best display quality.
- The repo already has a proven headless Chrome capture pattern in other labs, so this slice can reuse the same browser-based screenshot approach instead of introducing a new rendering dependency.
- A compact social-preview layout is a better fit than trying to squeeze the full long-form SVG into a small viewport, because the timeline artifacts are intentionally tall and text-heavy.

## Scope chosen for this slice
- add a compact HTML social-preview renderer derived from the termination timeline data
- capture that preview to PNG with headless Chrome via a first-class CLI flag
- regenerate the blocked-case artifact bundle and surface PNG links in the catalog/dashboard so the new assets are discoverable

## Sources used
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview
- existing repo PNG capture pattern in `projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py`

## Deferred
- cross-scenario gallery page for all blocked-case PNG covers
- auto-cropping or alternate aspect-ratio presets beyond the initial `1280x640` default
