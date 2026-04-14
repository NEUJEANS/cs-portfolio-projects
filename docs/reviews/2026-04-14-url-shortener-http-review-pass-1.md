# Review Pass 1 — url-shortener-http — 2026-04-14

## Focus
Correctness and resource hygiene after the first implementation pass.

## Findings
1. SQLite connections were used as context managers but not explicitly closed; `sqlite3.Connection.__exit__` commits/rolls back but does not close the connection.
2. HTTP test requests produced `ResourceWarning` noise because redirect/error objects were not being closed explicitly.

## Fixes applied
- Wrapped SQLite connections with `contextlib.closing(...)` and added explicit commits where writes occur.
- Refactored HTTP test helper to always read and close responses/errors cleanly.
- Re-ran tests with `PYTHONWARNINGS=error::ResourceWarning`.

## Result
Pass 1 issues fixed.
