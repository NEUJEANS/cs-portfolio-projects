# Review Pass 2 — Log Analyzer

## Focus
Edge cases and test coverage.

## Findings
1. Missing byte fields represented as `-` needed explicit handling.
2. The project lacked tests for malformed lines and CLI output modes.

## Fixes applied
- Normalized `-` byte counts to `0`.
- Added unit tests for malformed lines, empty results, JSON output, and text output.
