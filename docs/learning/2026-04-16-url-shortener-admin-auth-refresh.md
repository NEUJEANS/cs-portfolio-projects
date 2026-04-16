# URL shortener admin/auth refresh

- API-key-protected admin routes should return `401 Unauthorized` when the key is missing or invalid; `403` is more appropriate only after authentication succeeds but the caller still lacks permission.
- For a lightweight portfolio demo, threading one optional admin key through stdlib HTTP, WSGI, and container env vars is enough to show deployability without dragging in a full auth stack.
- Header-driven auth needs explicit propagation in WSGI (`HTTP_X_ADMIN_KEY`) and should preserve backward-compatible public redirect behavior.
- A quick self-test target for this slice: prove owner assignment is blocked without the admin key, while redirect lookups still work anonymously.
