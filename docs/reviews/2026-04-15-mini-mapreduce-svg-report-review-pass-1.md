# Review pass 1 — mini-mapreduce SVG report charts

## Focus
Code-path review of the new HTML chart generation helpers.

## Findings
1. The HTML report needed explicit semantic labels for the new SVG blocks so the artifact stayed explainable outside the source code.
2. The chart output needed deterministic dimensions so repo-level tests could assert the export shape reliably.

## Fixes applied
- added `<title>` and `aria-label` text to the timing and reducer-load SVG blocks
- used fixed `viewBox` dimensions with predictable chart sizing and centered bars

## Result
The exported HTML report now carries self-describing SVG charts that remain testable and screenshot-friendly.
