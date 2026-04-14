# url-shortener-http

## Overview
A local HTTP URL shortener backed by SQLite. It exposes a small JSON API for creating short links, a redirect endpoint for resolving them, and lightweight analytics for portfolio-friendly backend discussion.

## Why it is portfolio-worthy
- combines HTTP server design, persistence, routing, validation, and schema migration
- uses stable digest-based short-code generation instead of process-randomized Python `hash()`
- supports memorable custom aliases while protecting reserved route names
- demonstrates analytics/stateful behavior with redirect click tracking and metadata endpoints
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
- redirect support via `GET /<code>` with click tracking
- root health/stats endpoint at `GET /`
- dedicated analytics endpoint at `GET /stats`
- per-link metadata endpoint at `GET /links/<code>`
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

Create a custom alias:

```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/portfolio","code":"portfolio"}'
```

Example response:

```json
{
  "code": "portfolio",
  "short_url": "http://127.0.0.1:8000/portfolio",
  "url": "https://example.com/portfolio",
  "clicks": 0
}
```

Check service stats:

```bash
curl -s http://127.0.0.1:8000/stats
```

Inspect one link:

```bash
curl -s http://127.0.0.1:8000/links/portfolio
```

Resolve a short link:

```bash
curl -i http://127.0.0.1:8000/portfolio
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- expiration / deletion support
- deployable WSGI/ASGI wrapper plus Docker packaging
- admin/auth layer for multi-user management
- QR-code generation or batch import/export for demo use
