# Review Pass 1 — deadlock-detector-lab Banker's slice

## Checks
- read the new Banker's algorithm implementation and tests
- reran the unit suite while adding request coverage

## Issue found
- the first unsafe-request test case was actually safe, so it would have created a misleading regression test

## Fix applied
- replaced the request fixture with `P0` requesting `{A: 0, B: 0, C: 2}`, which correctly forces an unsafe post-grant state
