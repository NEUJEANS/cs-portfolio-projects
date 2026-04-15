# Python refresh — WSGI + deployment self-test

## Quick refresh
- WSGI apps receive `environ` + `start_response` and return an iterable of byte chunks.
- `PATH_INFO`, `QUERY_STRING`, `REQUEST_METHOD`, and `wsgi.input` are the key pieces needed for this project.
- `HTTP_HOST` should be preferred for externally visible links; otherwise fall back to server name/port.
- Keep transport-specific code thin so tests can exercise the shared request logic directly.

## Self-test
- Can I build one handler that returns `{status, headers, body}` and adapt both HTTP and WSGI to it? Yes.
- Can the existing JSON/redirect behavior stay identical while adding WSGI support? Yes, if both adapters call the same request dispatcher.
- Does Docker need anything more than a slim Python base, `gunicorn`, and a configurable DB path? Not for this slice.
