# Static-site-generator reviewer callouts review — pass 3

## Focus
Legacy test-entrypoint parity and end-to-end regression coverage.

## Issue found
- The mirrored compatibility suite `test_static_site_generator.js` drifted behind `sitegen.test.js`, so the new callout assertions only exercised the primary test entrypoint at first.

## Fix applied
- Synced `test_static_site_generator.js` with the updated primary suite.
- Reran the legacy direct test entrypoint after syncing.

## Result
- Both maintained test entrypoints now cover the reviewer/architecture callout slice consistently.
