# Markdown Notes Search Review Pass 1

Date: 2026-04-14

## Checks
- ran project unit tests
- manually exercised phrase and boolean CLI queries

## Issue found
- pure negative queries like `NOT archived` could match valid notes but end up with a weak scoring path tied to the raw query string rather than the actual exclusion logic

## Fix applied
- added fallback scoring for negative-only boolean matches
- added automated regression coverage for `NOT archived`

## Result
- boolean filter behavior is now stable for positive and negative-only queries
