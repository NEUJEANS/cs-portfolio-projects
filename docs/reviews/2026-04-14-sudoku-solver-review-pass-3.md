# 2026-04-14 sudoku-solver review pass 3

## Focus
Docs/tests alignment and user-facing error clarity.

## Findings
- the invalid-input smoke test originally surfaced a generic length error instead of naming the actual bad character
- README needed to match the stricter parser behavior so demos do not imply arbitrary characters are tolerated

## Fixes
- confirmed the parser now reports the exact invalid character in CLI output
- updated README feature wording to say stray non-board characters are rejected
- kept dedicated tests for invalid-character, invalid-board, missing-file, and compact-output flows

## Validation
- `python3 -m unittest discover -s projects/sudoku-solver -p 'test_*.py'` -> pass
- invalid-character CLI smoke test -> exits `2` with `board contains invalid characters: 'a'`
