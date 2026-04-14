# Expense Tracker Review Pass 3 — 2026-04-14

## Focus
CLI failure mode and polish.

## Issue found
Invalid input raised raw Python tracebacks, which looked unpolished for a portfolio CLI.

## Fix
- wrapped command execution in `try/except ValueError`
- return a clean `error: ...` message instead of a traceback
- added a CLI test for invalid negative amounts
