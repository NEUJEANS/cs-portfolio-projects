# Review pass 3 — url-shortener-http WSGI + Docker

## Focus
HTTP semantics and test completeness after the refactor.

## Issues found
- The project lacked adapter-level tests for WSGI error handling and host-aware `short_url` generation.
- The `/links/<code>` route needed explicit adapter-parity coverage for unsupported methods after the routing refactor.

## Fix applied
- Added WSGI tests for JSON error responses and host-aware URL generation.
- Added coverage for `POST /links/<code>` returning `405 Method Not Allowed` with the correct `Allow` header.
