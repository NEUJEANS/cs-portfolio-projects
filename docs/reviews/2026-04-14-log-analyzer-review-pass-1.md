# Review Pass 1 — Log Analyzer

## Focus
Parser correctness and feature completeness.

## Findings
1. Previous implementation used loose regex searches and could count malformed lines as valid IP rows.
2. Output was a raw Python dictionary, which is not a polished CLI experience.

## Fixes applied
- Added `parse_line()` with a structured common-log regex.
- Count only valid lines toward request metrics.
- Added formatted text output and optional JSON output.
