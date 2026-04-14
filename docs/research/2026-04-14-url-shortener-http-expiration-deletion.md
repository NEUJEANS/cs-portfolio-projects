# URL shortener HTTP research — expiration + deletion slice

Date: 2026-04-14
Project: `url-shortener-http`

## What I checked
- HTTP semantics for links that used to exist but should no longer redirect.
- Lightweight management endpoint patterns for small internal CRUD-style APIs.
- SQLite-friendly timestamp handling for a minimal portfolio project.

## Practical takeaways
1. `410 Gone` is a better fit than `404 Not Found` when a short code is known but intentionally unusable because it expired or was deleted.
2. Soft deletion is more portfolio-friendly than hard deletion here because analytics and lifecycle metadata remain inspectable.
3. A simple `DELETE /links/<code>` endpoint is enough for local management as long as the README clearly frames the current service as a local/demo backend without auth.
4. SQLite `CURRENT_TIMESTAMP` plus `datetime(CURRENT_TIMESTAMP, '+N seconds')` is enough for a clean, dependency-light expiration flow.
5. Stats become more informative when they separate active, expired, and deleted links instead of only total links/clicks.

## Slice choice
Implement an expiration/deletion lifecycle slice instead of packaging/auth first because it strengthens backend API design, state modeling, and HTTP semantics while staying compact and testable.
