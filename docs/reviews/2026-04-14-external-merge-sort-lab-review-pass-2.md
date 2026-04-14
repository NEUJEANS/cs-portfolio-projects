# external-merge-sort-lab review pass 2 - 2026-04-14

## Focus
Edge cases and output formatting.

## Findings
- empty input produced a trailing newline through the shared file writer path.

## Fixes made
- updated `write_numbers` to avoid writing a newline for empty output
- added an empty-input regression test
