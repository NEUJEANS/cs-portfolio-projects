# Review pass 1 — merkle-sync apply slice

## Focus
Code-path review for plan execution semantics and safety.

## Issues found
1. `apply --execute` from a manifest-only source would have raised a Python traceback instead of a clean CLI error.

## Fixes made
- Wrapped the apply execution path in `main()` with `parser.exit(2, ...)` so the CLI now fails fast with a readable error message.
- Added a regression test covering manifest-only execution rejection.

## Result
Execution mode now behaves like a real CLI tool instead of exposing an internal exception.
