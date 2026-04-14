# bloom-filter-cli review pass 2 — 2026-04-14

## Focus
Behavior consistency across JSON and binary artifacts.

## Findings
1. The main loader needed to auto-detect binary artifacts so existing CLI commands could work unchanged.
2. `remove` needed to preserve artifact type after mutating a counting filter.

## Fixes made
- Updated `load_filter` to detect the binary magic header automatically.
- Updated `remove` to rewrite `.bf` artifacts in binary and JSON files in JSON.
