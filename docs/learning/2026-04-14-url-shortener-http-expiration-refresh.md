# URL shortener HTTP refresh — timestamps + lifecycle states

Date: 2026-04-14
Project: `url-shortener-http`

## Refresher notes
- `http.server.BaseHTTPRequestHandler` can cleanly support lifecycle-oriented APIs with explicit `do_POST`, `do_GET`, and `do_DELETE` branches.
- SQLite `CURRENT_TIMESTAMP` returns UTC text in a lexicographically sortable format, so simple string comparison works for same-format expiration checks.
- `datetime(CURRENT_TIMESTAMP, '+60 seconds')` is a convenient dependency-free way to persist expiry timestamps.
- `410 Gone` communicates that a resource is intentionally unavailable after previously existing.

## Self-test
1. If a short code exists but is expired, should redirect return `404` or `410`? → `410`.
2. Why prefer soft delete here? → keeps metadata/history available for inspection and portfolio discussion.
3. How can we track lifecycle state without extra services? → store `expires_at` and `deleted_at` in SQLite and derive active/expired/deleted status.
4. What should stats show beyond total links? → active, expired, deleted, and click totals.
