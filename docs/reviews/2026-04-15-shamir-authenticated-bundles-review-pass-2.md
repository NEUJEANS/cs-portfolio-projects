# Review pass 2 — shamir authenticated bundles

## Checks
- reviewed inspect/recover JSON output for operator clarity
- checked README examples against actual CLI behavior

## Issue found
- it was too easy to inspect an authenticated bundle without knowing whether verification had actually happened

## Fix
- added `authenticated` and `authentication_verified` fields to inspect output
- updated README examples to show both authenticated split and authenticated inspect/recover flows
