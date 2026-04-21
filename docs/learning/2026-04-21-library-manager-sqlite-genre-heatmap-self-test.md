# library-manager-sqlite genre heatmap self-test

Date: 2026-04-21

## Quick refresh
- A separate `genre-heatmap` export is safer than changing the existing `genre-trends` CSV because it preserves the older artifact contract.
- Heatmap cells should expose a simple primary metric, here active-loan count, while supporting context such as share can ride along in tooltips and summary columns.
- Sequential light-to-dark fills are easier to read in static portfolio screenshots than multi-hue encodings that try to carry too many meanings at once.

## Self-test
1. Why keep active-loan count as the main heatmap color signal instead of using share alone?
   - Because count is easier to read at a glance and matches the interview question of where the load actually is. Share is still valuable, but it works better as secondary context.
2. Why add a new command instead of extending `genre-trends` output in place?
   - Because the old export already has a stable CSV shape and a separate recruiter-friendly SVG. A new command avoids breaking existing artifacts while still adding a stronger portfolio view.
3. Why include `total_active_selected` in each CSV row?
   - Because active share is only interpretable when the per-day denominator is visible. Including the daily selected-genre total keeps the CSV self-contained for spreadsheet follow-up.
