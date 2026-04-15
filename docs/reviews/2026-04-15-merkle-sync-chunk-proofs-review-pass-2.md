# Review Pass 2 — merkle-sync-lab chunk-proof slice

## Checks
- walked through odd-leaf and file-growth cases by hand
- inspected the changed-chunk JSON shape for downstream usability

## Issue found
- source growth was not covered by tests, so chunk additions beyond the target length could regress unnoticed

## Fix applied
- added `test_chunk_diff_handles_source_growth` to lock in appended-chunk reporting
