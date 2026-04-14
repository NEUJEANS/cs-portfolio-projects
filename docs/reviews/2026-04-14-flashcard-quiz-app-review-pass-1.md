# Flashcard Quiz App Review Pass 1

## Focus
CLI failure behavior and input validation UX.

## Findings
1. Invalid CSV input would raise a raw Python traceback in `main()`, which is too rough for a portfolio CLI.

## Fixes Applied
- wrapped session setup in `main()` with `try/except ValueError`
- converted validation failures into a clean argparse exit with code 2 and a readable `Error: ...` message
- added an automated test covering the invalid-CSV CLI path

## Result
CLI now fails cleanly for malformed decks instead of dumping an implementation traceback.
