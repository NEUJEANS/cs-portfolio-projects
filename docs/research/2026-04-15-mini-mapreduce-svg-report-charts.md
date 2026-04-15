# Mini MapReduce SVG report chart notes

## Why no external web research this slice
The existing mini-mapreduce benchmark docs and README already scoped the next gap clearly: the HTML report had good tables and heatmaps, but no quick visual summary for portfolio screenshots. That made a compact internal follow-up more useful than broad external research.

## Slice target
Add lightweight inline SVG charts to the standalone HTML benchmark report so one exported file can show:
- elapsed benchmark timing by reducer count
- total records handled by each reducer for a selected reducer-count section

## Constraints
- keep the artifact self-contained with no JS or external chart libraries
- preserve deterministic output for tests
- use semantic SVG titles/labels so the exported page remains explainable and accessible
