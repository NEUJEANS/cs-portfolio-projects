# Review pass 2 — mini-mapreduce SVG report charts

## Focus
Artifact review of generated HTML output.

## Checks
- generated a fresh benchmark HTML report from the CLI
- inspected chart headings and embedded SVG titles
- verified reducer-specific sections still include the heatmap table after the chart block

## Findings
1. The timing chart should appear as a first-class artifact section, not as hidden markup buried between tables.
2. Reducer-load charts should be visually grouped with each reducer section to keep the export readable.

## Fixes applied
- wrapped both SVG outputs in reusable `chart-card` containers
- added visible `Elapsed timing chart` and `Reducer load chart` headings

## Result
The standalone HTML export now reads like a portfolio artifact instead of a raw table dump.
