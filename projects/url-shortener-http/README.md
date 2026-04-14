# url-shortener-http

## Overview
A local HTTP URL shortener backed by SQLite. It exposes a small JSON API for creating short links, redirecting them, inspecting link metadata, and managing lifecycle states such as expiration and soft deletion.

## Why it is portfolio-worthy
- combines HTTP server design, persistence, routing, validation, schema migration, and API lifecycle semantics
- uses stable digest-based short-code generation instead of process-randomized Python `hash()`
- supports memorable custom aliases while protecting reserved route names
- demonstrates stateful backend behavior with analytics, expiration, deletion, and metadata inspection
- uses both unit tests and live HTTP integration tests

## Stack
- Python 3
- `http.server` for the web layer
- SQLite for persistence
- `unittest` for unit and integration tests

## Features
- `POST /shorten` JSON API with validation and explicit error responses
- deterministic short-code generation with collision retry handling
- optional custom aliases via `code` in the request body
- optional per-link expiry via `expires_in_seconds`
- redirect support via `GET /<code>` with click tracking
- `410 Gone` responses for expired or deleted short codes
- root health/stats endpoint at `GET /`
- dedicated analytics endpoint at `GET /stats`
- per-link metadata endpoint at `GET /links/<code>`
- soft deletion endpoint at `DELETE /links/<code>`
- route-specific `405 Method Not Allowed` handling for `/shorten`

## Usage
Start the server:

```bash
python3 url_shortener.py --db shortener.db --port 8000
```

Create a digest-based short link:

```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/coursework"}'
```

Create a custom alias with expiry:

```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/demo","code":"demo-link","expires_in_seconds":3600}'
```

Example response:

```json
{
  "code": "demo-link",
  "short_url": "http://127.0.0.1:8000/demo-link",
  "url": "https://example.com/demo",
  "clicks": 0,
  "status": "active",
  "expires_at": "2026-04-14 23:00:00"
}
```

Check service stats:

```bash
curl -s http://127.0.0.1:8000/stats
```

Inspect one link:

```bash
curl -s http://127.0.0.1:8000/links/demo-link
```

Delete a short link without erasing its metadata history:

```bash
curl -s -X DELETE http://127.0.0.1:8000/links/demo-link
```

Resolve a short link:

```bash
curl -i http://127.0.0.1:8000/demo-link
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- deployable WSGI/ASGI wrapper plus Docker packaging
- admin/auth layer for multi-user management
- QR-code generation or batch import/export for demo use
