# 2026-04-21 Consistent Hashing Visualization Self-Test

## Refresher
- A ring visualization is only trustworthy if it reuses the exact hash positions and assignments already used by the CLI logic.
- Showing every key on the ring usually hurts readability, so it is better to plot a deterministic subset while still computing load metrics from the full key set.
- SVG is ideal for deterministic, committed artifacts because it is diffable, self-contained, and easy to wrap in HTML later.

## Quick self-test
1. Why should the visualization reuse the existing assignment logic instead of recomputing ownership separately? So the visual artifact cannot drift from the CLI's actual behavior.
2. Why keep `--displayed-key-count` separate from the total key count? So the chart stays readable while the load report still reflects the full workload.
3. Why keep stdout JSON even when writing SVG and HTML files? So scripts and tests can still inspect the deterministic summary without scraping the rendered artifacts.
