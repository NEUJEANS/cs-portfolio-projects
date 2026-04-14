# URL Shortener HTTP Upgrade Research — 2026-04-14

## Goal
Upgrade `url-shortener-http` from a minimal demo into a stronger portfolio slice with safer URL handling, deterministic short-code generation, and more realistic HTTP API behavior.

## Brief findings
- `BaseHTTPRequestHandler` is enough for a small portfolio project if responses are explicit and consistent.
- Invalid JSON should return `400 Bad Request` with a machine-readable JSON error body.
- Unsupported methods should return `405 Method Not Allowed` and include an `Allow` header.
- Basic URL validation can be done with `urllib.parse.urlparse()` by requiring an `http`/`https` scheme plus a non-empty host.
- Python built-in `hash()` is process-randomized, so it is a weak choice for persistent short-code generation. A stable digest-based approach is better.

## Sources used
- Python docs: `http.server`
- Python docs: `urllib.parse`
- MDN: HTTP 405 Method Not Allowed
- General REST/API response guidance from Stack Overflow / Stack Overflow Blog search results

## Planned vertical slice
1. Replace `hash(url)` codes with deterministic SHA-256-based code generation plus collision handling.
2. Add input validation and JSON error responses.
3. Add HTTP routing behavior for `GET /`, `POST /shorten`, and unsupported methods on known routes.
4. Expand tests to cover validation, collision-safe storage, and live HTTP behavior.
5. Update README and project checklist.
