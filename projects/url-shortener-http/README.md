# url-shortener-http

## Overview
A local HTTP URL shortener backed by SQLite. It exposes a small JSON API for creating short links, redirecting them, inspecting link metadata, and managing lifecycle states such as expiration and soft deletion. This slice also adds a reusable WSGI deployment entrypoint and Docker packaging so the project is easier to demo beyond a single local script run.

## Why it is portfolio-worthy
- combines HTTP server design, persistence, routing, validation, schema migration, and API lifecycle semantics
- uses stable digest-based short-code generation instead of process-randomized Python `hash()`
- supports memorable custom aliases while protecting reserved route names
- demonstrates stateful backend behavior with analytics, expiration, deletion, and metadata inspection
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
- optional per-link expiry via `expires_in_seconds`
- redirect support via `GET /<code>` with click tracking
- `410 Gone` responses for expired or deleted short codes
- root health/stats endpoint at `GET /`
- dedicated analytics endpoint at `GET /stats`
- per-link metadata endpoint at `GET /links/<code>`
- soft deletion endpoint at `DELETE /links/<code>`
- route-specific `405 Method Not Allowed` handling
- `wsgi.py` entrypoint for Gunicorn or other WSGI servers
- Docker packaging with configurable persistent SQLite path via `SHORTENER_DB`

## Usage
### Run the built-in HTTP server
```bash
python3 url_shortener.py --db shortener.db --port 8000
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

### Check service stats
```bash
curl -s http://127.0.0.1:8000/stats
```

### Inspect one link
```bash
curl -s http://127.0.0.1:8000/links/demo-link
```

### Delete a short link without erasing its metadata history
```bash
curl -s -X DELETE http://127.0.0.1:8000/links/demo-link
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
SHORTENER_DB=shortener.db gunicorn --bind 127.0.0.1:8000 wsgi:app
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
  -v "$PWD/data:/data" \
  url-shortener-http
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- admin/auth layer for multi-user management
- QR-code generation or batch import/export for demo use
- ASGI adapter if the project grows into async middleware or websockets
