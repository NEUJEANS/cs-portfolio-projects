# url-shortener-http Checklist

## Current slice — 2026-04-14
- [x] identify this as the weakest unfinished project in the repo set
- [x] do brief HTTP/API behavior research
- [x] refresh Python `http.server`, `urllib.parse`, and digest-generation basics
- [x] replace unstable `hash(url)` code generation with deterministic digest-based codes
- [x] add URL validation with clear 400-level error messages
- [x] add root stats endpoint and route-specific 405 handling
- [x] expand tests to cover store behavior, collisions, validation, and live HTTP requests
- [x] update README with examples and stronger portfolio framing
- [ ] add custom aliases
- [ ] add analytics / click counts
- [ ] add expiration / deletion support
- [ ] add deployment packaging

## Quality bar
- [x] implementation complete for this slice
- [x] README included
- [x] usage examples included
- [x] tests included
- [x] at least 3 review passes logged
- [x] future improvements listed
