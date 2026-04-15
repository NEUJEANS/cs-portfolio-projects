# Review pass 2 — url-shortener-http WSGI + Docker

## Focus
Deployment ergonomics and externally visible link generation.

## Issue found
- A deployment entrypoint without a configurable DB path would make Docker demos awkward and encourage writing SQLite state inside the container filesystem.

## Fix applied
- Added `SHORTENER_DB` support in `wsgi.py`.
- Documented mounted-volume Docker usage in the README.
- Added Docker packaging files (`Dockerfile`, `.dockerignore`, `requirements.txt`).
