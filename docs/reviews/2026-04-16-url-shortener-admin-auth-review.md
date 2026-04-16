# URL shortener admin/auth review — 2026-04-16

## Review pass 1 — diff audit
- Checked the slice diff for routing, auth gating, schema migration, and README alignment.
- Found one route-shape bug: `/owners/<owner>/links/extra` was falling into owner validation and returning `400` instead of `404`.
- Fix applied: tightened `/owners/<owner>/links` parsing so only the exact route shape is accepted.

## Review pass 2 — smoke checks
- Created an owner-scoped link with an admin key through `UrlShortenerApp`.
- Verified `GET /stats?owner=alice` returns owner-filtered stats.
- Verified public redirect resolution still works without auth.
- Verified metadata access without `X-Admin-Key` returns `401` plus `WWW-Authenticate`.
- Verified WSGI mode also returns the same auth challenge for admin routes.

## Review pass 3 — docs/consistency audit
- Grepped README, checklist, and implementation for `admin`, `owner`, `X-Admin-Key`, and `SHORTENER_ADMIN_KEY` references.
- Confirmed the docs mention the new protected routes, env vars, and owner examples consistently.
- Confirmed the checklist records the slice and remains resumable.
