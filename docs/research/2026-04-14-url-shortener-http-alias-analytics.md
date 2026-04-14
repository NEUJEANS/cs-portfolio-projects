# URL Shortener HTTP Research — Alias + Analytics Slice

Date: 2026-04-14

## Goal
Strengthen `url-shortener-http` with a more interview-ready backend slice: memorable custom aliases plus basic click analytics.

## Brief notes
- A student-friendly shortener becomes easier to demo when links can use human-readable aliases instead of only generated digests.
- Aliases need validation and reserved-word protection so route names like `/shorten` and `/stats` stay usable.
- A minimal analytics slice does not need dashboards; redirect click counts plus a metadata endpoint are enough to show stateful HTTP behavior.
- SQLite schema evolution is worth demonstrating here because small backend projects often need additive migrations over time.

## Sources used
- Python docs: `sqlite3`
- Python docs: `http.server`
- MDN references for redirect behavior and status-code expectations
- general prior backend/API knowledge; no extra web search was necessary beyond standard references

## Scope chosen
1. accept optional custom `code` values on `POST /shorten`
2. validate aliases and reject reserved route names
3. track redirect clicks and last access time
4. add `GET /stats` and `GET /links/<code>` endpoints
5. expand tests and README to cover the stronger slice
