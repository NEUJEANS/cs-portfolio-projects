# Flashcard quiz app review pass 1 — 2026-04-14

## Focus
CLI behavior and persistence ergonomics.

## Findings
1. `--show-history-summary` could be requested without `--history-path`, which would make the flag silently useless.

## Fixes applied
- Added explicit validation so the CLI exits with a clear error when `--show-history-summary` is used without `--history-path`.
- Added a regression test for that argument combination.
