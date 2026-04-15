# Review pass 1 — url-shortener-http WSGI + Docker

## Focus
Shared request-dispatch correctness between the stdlib HTTP server and the new WSGI adapter.

## Issue found
- The new deployable path would be fragile if HTTP and WSGI each implemented routing separately.

## Fix applied
- Centralized request handling in `UrlShortenerApp.handle_request(...)` and made both adapters delegate to it.
- Added WSGI tests to verify create + redirect parity.
