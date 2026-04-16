# Review Pass 2 — link-state routing suite

## Focus
Artifact and DX review for checked-in benchmark outputs.

## Issues found
1. CSV output used purely alphabetical columns, which made the summary harder to scan in GitHub and spreadsheet tools.

## Fixes applied
- Added a preferred CSV column order so scenario name, event type, routing settings, and before/after metrics appear first.

## Result
Generated benchmark artifacts are easier to read and compare at a glance.
