# url-shortener-http Vertical Slice — 2026-04-15 WSGI + Docker

- [x] confirm `url-shortener-http` is still one of the weaker unfinished backend portfolio projects because it lacked a deployable entrypoint
- [x] do brief deployment-oriented research on WSGI entrypoints and container packaging expectations
- [x] do a short Python WSGI/self-test refresh before refactoring request handling
- [x] update checklist/docs so the slice is resumable
- [x] refactor request handling into reusable application logic shared by the stdlib HTTP server and a WSGI wrapper
- [x] add a `wsgi.py` entrypoint plus deployment metadata for Gunicorn-based serving
- [x] add Docker packaging files for local/demo deployment
- [x] expand tests to cover WSGI request handling in addition to the existing live HTTP server tests
- [x] run tests locally
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
