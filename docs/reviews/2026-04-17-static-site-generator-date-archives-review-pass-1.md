# Review pass 1 — static-site-generator date archives

## What I checked
- archive page generation wiring in `buildSite`
- test coverage for the new yearly archive flow
- compatibility with the mirrored legacy test entrypoint

## Issue found
- the mirrored `test_static_site_generator.js` file still reflected the pre-archive behavior, so the duplicate entrypoint no longer matched the maintained test suite

## Fix applied
- synced `test_static_site_generator.js` with `sitegen.test.js`
- kept the new archive assertions in both entrypoints so `npm test` and the legacy direct invocation stay aligned
