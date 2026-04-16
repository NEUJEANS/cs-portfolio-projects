# url-shortener-http

## Overview
A local HTTP URL shortener backed by SQLite. It exposes a small JSON API for creating short links, redirecting them, inspecting link metadata, and managing lifecycle states such as expiration and soft deletion. This slice adds an optional admin API key and owner-scoped management endpoints so the project can demo lightweight multi-user operations without giving up a simple public redirect flow.

## Why it is portfolio-worthy
- combines HTTP server design, persistence, routing, validation, schema migration, and API lifecycle semantics
- uses stable digest-based short-code generation instead of process-randomized Python `hash()`
- supports memorable custom aliases while protecting reserved route names
- demonstrates stateful backend behavior with analytics, expiration, deletion, and metadata inspection
- adds an optional admin API key plus owner tagging for safer multi-user management demos
- reuses one request-dispatch layer across both stdlib HTTP and WSGI deployment paths
- ships unit tests, live HTTP integration tests, WSGI adapter tests, and a containerized deployment path

## Stack
- Python 3
- `http.server` for the local web layer
- WSGI-compatible adapter for production-style serving
- SQLite for persistence
- `unittest` for unit and integration tests
- Gunicorn + Docker for packaging/demo deployment

## Features
- `POST /shorten` JSON API with validation and explicit error responses
- deterministic short-code generation with collision retry handling
- optional custom aliases via `code` in the request body
- optional owner tagging via `owner` for multi-user demo environments
- optional per-link expiry via `expires_in_seconds`
- redirect support via `GET /<code>` with click tracking
- `410 Gone` responses for expired or deleted short codes
- root health/stats endpoint at `GET /`
- admin-protected analytics endpoint at `GET /stats` with optional `?owner=` filter
- admin-protected per-link metadata endpoint at `GET /links/<code>`
- admin-protected owner listing endpoint at `GET /owners/<owner>/links`
- soft deletion endpoint at `DELETE /links/<code>`
- route-specific `405 Method Not Allowed` handling
- `wsgi.py` entrypoint for Gunicorn or other WSGI servers
- Docker packaging with configurable persistent SQLite path via `SHORTENER_DB` and `SHORTENER_ADMIN_KEY`

## Usage
### Run the built-in HTTP server
```bash
python3 url_shortener.py --db shortener.db --port 8000 --admin-key supersecret
```

### Create a digest-based short link
```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/coursework"}'
```

### Create a custom alias with expiry
```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/demo","code":"demo-link","expires_in_seconds":3600}'
```

### Create an owner-scoped link when admin mode is enabled
```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -H 'X-Admin-Key: supersecret' \
  -d '{"url":"https://example.com/team-demo","code":"team-demo","owner":"alice"}'
```

Example response:

```json
{
  "code": "demo-link",
  "short_url": "http://127.0.0.1:8000/demo-link",
  "url": "https://example.com/demo",
  "owner": "public",
  "clicks": 0,
  "status": "active",
  "expires_at": "2026-04-14 23:00:00"
}
```

### Check service stats in admin mode
```bash
curl -s http://127.0.0.1:8000/stats \
  -H 'X-Admin-Key: supersecret'
```

### Inspect one link
```bash
curl -s http://127.0.0.1:8000/links/demo-link \
  -H 'X-Admin-Key: supersecret'
```

### List links for one owner
```bash
curl -s "http://127.0.0.1:8000/owners/alice/links?limit=10" \
  -H 'X-Admin-Key: supersecret'
```

### Delete a short link without erasing its metadata history
```bash
curl -s -X DELETE http://127.0.0.1:8000/links/demo-link \
  -H 'X-Admin-Key: supersecret'
```

### Resolve a short link
```bash
curl -i http://127.0.0.1:8000/demo-link
```

## WSGI deployment
Install the deployment dependency:

```bash
python3 -m pip install -r requirements.txt
```

Run with Gunicorn:

```bash
SHORTENER_DB=shortener.db SHORTENER_ADMIN_KEY=supersecret gunicorn --bind 127.0.0.1:8000 wsgi:app
```

## Docker deployment
Build the image:

```bash
docker build -t url-shortener-http .
```

Run it with a mounted data directory so SQLite state survives container restarts:

```bash
mkdir -p data
docker run --rm -p 8000:8000 \
  -e SHORTENER_DB=/data/shortener.db \
  -e SHORTENER_ADMIN_KEY=supersecret \
  -v "$PWD/data:/data" \
  url-shortener-http
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- per-owner API keys or role separation beyond one shared admin key
- QR-code generation or batch import/export for demo use
- ASGI adapter if the project grows into async middleware or websockets
