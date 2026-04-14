# bloom-filter-cli review pass 1 — 2026-04-14

## Focus
Implementation correctness for the new binary artifact format.

## Findings
1. Needed an explicit file header and version field so binary artifacts fail safely instead of being misread as JSON.
2. Needed payload-length validation so truncated files are rejected cleanly.

## Fixes made
- Added `BLMF` magic bytes and versioned header parsing.
- Added strict payload/header length validation in `load_filter_binary`.
