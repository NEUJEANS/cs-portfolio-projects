# Bloom Filter CLI Review Pass 3

## Focus
Docs, resumability, and test hygiene.

## Issues found
1. The checklist and README still described counting Bloom filters as a future idea instead of shipped functionality.
2. The test helper for JSON reloads used a fixed temporary filename, which could collide across runs.

## Fixes applied
- Updated the checklist, README, research note, and learning note to reflect the new counting-filter slice and next steps.
- Switched the JSON reload helper to `tempfile.NamedTemporaryFile` for safer resumable test runs.
- Re-ran the targeted unit suite and counting-filter CLI smoke tests after the doc and helper cleanup.
