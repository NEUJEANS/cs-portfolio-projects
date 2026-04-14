# URL Shortener HTTP Alias + Analytics Review — Pass 1

Date: 2026-04-14

## Focus
API correctness and deploy/demo friendliness.

## Issue found
- `short_url` response used a hard-coded `127.0.0.1` host, which made the generated URL inaccurate when the server was accessed through another host/port mapping.

## Fix applied
- Build `short_url` from the incoming `Host` header with a safe fallback to the bound server host/port.

## Result
- Better real-world behavior for demos and reverse-proxy/local-network use.
