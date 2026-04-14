# 2026-04-14 sudoku-solver review pass 1

## Focus
Code correctness and parser behavior.

## Findings
- the parser still silently dropped stray non-board characters, which could turn a typo into a misleading length error
- file reads relied on the platform default encoding instead of an explicit UTF-8 read

## Fixes
- reject non-whitespace characters outside `[0-9.]` with a clear `board contains invalid characters` error
- read board files with explicit UTF-8 encoding

## Validation
- `python3 -m unittest discover -s projects/sudoku-solver -p 'test_*.py'` -> pass
