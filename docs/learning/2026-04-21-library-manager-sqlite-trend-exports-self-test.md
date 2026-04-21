# library-manager-sqlite trend exports self-test

Date: 2026-04-21

## Quick refresh
- Python `datetime.date` arithmetic is enough for deterministic day-by-day ranges.
- Simple CSV output does not need extra dependencies when values are controlled ISO dates and integers.
- Accessible SVG should include a root `<title>` and `<desc>`, plus panel-level descriptive text when the chart contains multiple regions.

## Self-test
1. Why not default trend exports to only the latest snapshot?
   - Because the whole point of the slice is showing change over time, not just a point-in-time state.
2. Why use small multiples instead of one four-line chart?
   - The metrics have different scales and meanings, so separate panels reduce visual clutter and make interview walkthroughs easier.
3. What makes the committed artifacts reproducible?
   - Explicit `--start-date`, `--end-date`, and `--generated-at` arguments.
