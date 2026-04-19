# log-analyzer gallery controls research — 2026-04-19

## Goal
Make the committed facet-ranking gallery more presentation-ready without adding new Python/runtime dependencies or forcing users to regenerate the artifact for every minor viewing preference.

## Constraints
- project stays standard-library-only
- gallery output should remain one portable HTML file
- current gallery already has the right data; the weakness is usability once many facet slices exist
- follow-up should feel like a real vertical slice, not a cosmetic-only tweak

## Decision
Prefer progressive enhancement inside the exported HTML over new CLI-only filter flags.

Why:
- students can open one committed artifact and explore it immediately in-browser
- static client-side controls keep GitHub Pages / local file usage simple
- no raster/export dependency is required
- sort/filter behavior can evolve without changing the underlying analysis pipeline

## Implementation direction
- expose per-slice request-volume metadata (`facet_total_count`) in the existing facet ranking rows
- render per-card request-volume + populated-family summary chips
- add in-browser search, exact per-field selects, sort presets, and a hide-empty toggle
- keep all controls self-contained so committed docs artifacts remain portable

## Deferred
- PNG export helpers
- deep-link/shareable filter state
- per-facet downloadable detail bundles
