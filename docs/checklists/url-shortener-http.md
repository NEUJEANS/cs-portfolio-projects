# url-shortener-http Checklist

## Current slice — 2026-04-14
- [x] identify this as the weakest unfinished project in the repo set
- [x] do brief HTTP/API behavior research
- [x] refresh Python `http.server`, `urllib.parse`, and digest-generation basics
- [x] replace unstable `hash(url)` code generation with deterministic digest-based codes
- [x] add URL validation with clear 400-level error messages
- [x] add root stats endpoint and route-specific 405 handling
- [x] expand tests to cover store behavior, collisions, validation, and live HTTP requests
- [x] update README with examples and stronger portfolio framing

## Vertical slice 2 — 2026-04-14 alias + analytics
- [x] identify `url-shortener-http` as still one of the weaker backend projects because it lacked memorable aliases and stateful analytics
- [x] add brief research notes for alias validation, analytics, and SQLite schema evolution
- [x] do short Python/SQLite/http refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add custom aliases with reserved-route protection
- [x] add click counts, last-access timestamps, and stats/metadata endpoints
- [x] expand tests for alias validation, analytics, and HTTP behavior
- [x] update README with the stronger backend scope
- [x] run tests locally
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Vertical slice 3 — expiration + deletion lifecycle
- [x] confirm `url-shortener-http` is still worth one more backend slice because links could not expire or be retired cleanly
- [x] do brief research on expiration semantics, `410 Gone`, and management endpoint patterns
- [x] do short Python/SQLite timestamp refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add optional `expires_in_seconds` support with persisted `expires_at` metadata
- [x] return `410 Gone` for expired or deleted short codes while keeping metadata inspectable
- [x] add `DELETE /links/<code>` soft deletion and richer stats state counts
- [x] expand automated coverage for expiry validation, expired redirects, deletion, and stateful stats
- [x] run tests locally
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## Future improvements
- [x] expiration / deletion support
- [ ] deployable WSGI/ASGI wrapper plus Docker packaging
- [ ] admin/auth layer for multi-user management
