# Research note — robin-hood-hashing-lab lookup percentile slice

Date: 2026-04-21

## What I checked
- Reused the repo's existing percentile-summary pattern from `projects/extendible-hashing-lab/extendible_hashing_lab.py` so the new Robin Hood benchmark slice reports pooled `p50` and `p95` probe counts with the same deterministic, ceiling-rank percentile rule already used elsewhere in this portfolio repo.
- Confirmed the current Robin Hood benchmark already keeps full unsuccessful-lookup histograms, so the missing piece for side-by-side hit/miss tails was preserving successful-lookup probe distributions too.

## Decision
- Keep the slice focused on compact lookup tail callouts, not full successful-lookup histograms, so the report gets easier to read without ballooning the dashboard.
- Store successful-lookup probe histograms in the raw benchmark JSON/CSV outputs, then derive pooled avg/stddev/p50/p95/max summaries for the Markdown and HTML callout sections.
