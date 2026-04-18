# CRDT OR-Set Lab — preset detail-bundle research (2026-04-18)

## Goal
Finish the next obvious follow-up from the preset-suite slice: let each summary card jump straight into its own committed artifact bundle instead of stopping at the suite-level summary.

## Quick refresh
- Reuse the repo's existing artifact-export pattern instead of inventing a second rendering path just for presets.
- Keep links relative to the output file that references them so the generated Markdown/HTML/JSON stays portable on GitHub Pages, local file servers, and repo clones.
- Emit one detail bundle per preset with the same artifacts already proven useful elsewhere: comparison page, OR-Set timeline, replay page, anti-entropy report, and raw snapshot JSON.

## Implementation notes pulled into the slice
- Treat the preset registry as the source of truth and fan out detail bundles from `compare-presets` rather than adding another top-level command.
- Centralize relative-path calculation so suite Markdown, suite HTML, suite JSON, and CLI stdout can each choose the right base directory without duplicating string math.
- Attach bundle metadata back onto each preset record (`detail_bundle`) so rendering stays data-driven and future outputs can reuse the same structure.

## Scope chosen
- add `--detail-output-dir` to `compare-presets`
- generate per-preset comparison/timeline/replay/anti-entropy/snapshot artifacts under that directory
- surface direct links in the suite Markdown/HTML/JSON outputs
- keep the slice narrow: no new CRDT semantics, only better artifact packaging and navigation

## Deferred
- a mini landing page or zip archive inside each preset bundle
- PNG/raster exports for slide decks
- broader CRDT family comparisons beyond the existing OR-Set vs LWW framing
