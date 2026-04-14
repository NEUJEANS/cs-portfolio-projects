# URL Shortener HTTP Refresh — 2026-04-14

## Quick refresher
- `BaseHTTPRequestHandler` gives per-method hooks such as `do_GET` and `do_POST`.
- `send_response`, `send_header`, and `end_headers` must be called in order before writing the body.
- `urlparse()` is sufficient for a basic first-pass URL validator in a local portfolio project.
- `hash()` is not stable across Python processes; `hashlib.sha256()` is the safer choice for persistent code generation.

## Self-check
- Can I return JSON with explicit status codes and content length? Yes.
- Can I distinguish `404` from `405` by route? Yes.
- Can I make short codes deterministic but still collision-safe? Yes: digest + suffix retry loop.
