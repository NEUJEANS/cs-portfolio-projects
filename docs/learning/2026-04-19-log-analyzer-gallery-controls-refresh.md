# log-analyzer gallery controls refresh — 2026-04-19

## Quick refresh
- `summarize_top_counts_by_facet(...)` now stamps each ranking row with `facet_total_count`, which carries the total request volume for that facet slice so downstream gallery code can sort and summarize cards without recomputing slice sizes.
- the facet ranking gallery uses that metadata to sort cards by traffic and to show per-card request-volume chips.
- the exported gallery is still static HTML, but now includes:
  - text search across facet labels/values
  - exact per-facet-field select filters
  - sort presets (`traffic-desc`, `traffic-asc`, `label-asc`, `label-desc`)
  - hide-empty ranking-family toggle
- filtering/sorting happens in inline browser JS; the underlying analysis result is unchanged.

## Self-test checklist
- make sure cards still render when referrer/user-agent families are empty
- make sure `data-facet-total-count` and `data-facet-map` land in the HTML
- make sure related links are still rewritten relative to the gallery output path
- make sure sample artifact remains usable directly from `docs/artifacts/log-analyzer/facet-ranking-gallery.html`
