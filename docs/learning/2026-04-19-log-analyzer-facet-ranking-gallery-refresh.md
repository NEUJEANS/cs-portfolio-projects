# Refresh / self-test — 2026-04-19 — log-analyzer facet ranking gallery

## Quick refresh
- Reuse the existing `top_*_by_facet` arrays instead of inventing a second analysis pipeline.
- Keep gallery links relocatable by rewriting local targets relative to the gallery output file, matching the preset-gallery behavior.
- Preserve the busiest-facet-first ordering already established by the ranking summarizers so screenshots remain stable and meaningful.

## Self-test plan
1. Add a formatter that groups ranking tables by facet slice and optionally appends related artifact links.
2. Add CLI coverage for successful gallery export plus validation errors (`--facet-ranking-gallery-link` without gallery output, gallery export without `--facet-field`).
3. Regenerate a committed gallery artifact from the existing sample combined-log file and confirm the output still matches the existing CSV exports.