# url-shortener-http

## Overview
A local HTTP URL shortener backed by SQLite. It exposes a tiny JSON API for creating short links and a redirect endpoint for resolving them.

## Why it is portfolio-worthy
- combines HTTP server design, persistence, routing, and validation
- uses stable digest-based short-code generation instead of process-randomized Python `hash()`
- demonstrates test coverage at both unit and live HTTP integration levels
- keeps scope realistic for a student project while leaving room for deploy/auth/analytics upgrades

## Stack
- Python 3
- `http.server` for the web layer
- SQLite for persistence
- `unittest` for unit and integration tests

## Features
- `POST /shorten` JSON API with validation and explicit error responses
- deterministic short-code generation with collision retry handling
- redirect support via `GET /<code>`
- root health/stats endpoint at `GET /`
- route-specific `405 Method Not Allowed` handling for `/shorten`

## Usage
Start the server:

```bash
python3 url_shortener.py --db shortener.db --port 8000
```

Create a short link:

```bash
curl -s http://127.0.0.1:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/coursework"}'
```

Example response:

```json
{
  "code": "a1b2c3d",
  "short_url": "http://127.0.0.1:8000/a1b2c3d",
  "url": "https://example.com/coursework"
}
```

Check service stats:

```bash
curl -s http://127.0.0.1:8000/
```

Resolve a short link:

```bash
curl -i http://127.0.0.1:8000/a1b2c3d
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- custom aliases and reserved-word protection
- click analytics and expiration windows
- deployable WSGI/ASGI wrapper plus Docker packaging
- admin/auth layer for multi-user management
