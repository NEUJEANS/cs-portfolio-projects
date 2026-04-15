# Review pass 1 — MinHash incremental refresh

## What I checked
- `python3 -m unittest tests.test_minhash_near_duplicate`
- new API and CLI coverage for `refresh-index`

## Finding
- No failing tests after adding refresh-path assertions.

## Outcome
- Kept the new refresh stats shape and JSON output unchanged.
