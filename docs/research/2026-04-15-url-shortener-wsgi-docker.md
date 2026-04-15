# url-shortener-http WSGI + Docker research

## Goal
Make the project easier to demo and deploy without replacing the existing stdlib HTTP implementation.

## Notes
- A small WSGI callable is enough for production-style serving because Gunicorn only needs an importable `module:callable` such as `wsgi:app`.
- Reusing one request-dispatch layer across both the stdlib HTTP server and WSGI paths prevents drift between local-demo behavior and deployable behavior.
- Container packaging should keep writable SQLite state outside the image when possible, so an environment variable such as `SHORTENER_DB` is a simple fit.
- For a portfolio project, shipping `Dockerfile`, `requirements.txt`, and a WSGI entrypoint tells a stronger story than only saying "could be deployed later." 
