# Review pass 2 — bloom-filter-cli

## Focus
CLI robustness and user input handling.

## Findings
1. Query items in the `check` subcommand were not normalized, so accidental whitespace could produce misleading results.

## Fixes applied
- Normalized query items with `strip()` and ignored blank inputs before membership checks.

## Verification
- `python3 projects/bloom-filter-cli/bloom_filter.py check --filter <generated-filter> apple kiwi`
