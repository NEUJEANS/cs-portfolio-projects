# Review pass 1 — url-shortener-http expiration/deletion slice

Date: 2026-04-14

## Focus
- lifecycle-state correctness
- HTTP semantics for expired/deleted links
- schema update safety

## Issue found
- Status derivation opened a fresh SQLite connection for each row inspection, which was unnecessary and especially wasteful during stats generation.

## Fix applied
- Added a reusable current-timestamp helper and passed one timestamp through row-status evaluation within the active connection.

## Result
- Lifecycle logic stayed correct and became cleaner/more efficient.
