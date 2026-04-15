# Wrap-up — 2026-04-15 20:42 UTC

## What changed
- added optional `--normalize-identifiers` support for MinHash `code` mode so renamed local identifiers collapse into the same near-duplicate fingerprint
- persisted normalization metadata in saved signature indexes so `build-index`, `scan-index`, and `refresh-index` remain resumable and consistent
- extended benchmark/report payloads to surface whether identifier normalization was enabled
- expanded repository tests for normalized code tokens, similarity deltas, CLI validation, export metadata, and saved-index round-trips
- updated the README, project checklist, slice checklist, learning note, and 3 review logs for the new vertical slice

## Tests and reviews run
- `python3 -m unittest tests.test_minhash_near_duplicate`
- `python3 -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- manual CLI smoke test covering `compare`, `build-index`, and `benchmark` with `--token-mode code --normalize-identifiers`
- `git diff --check`
- review pass 1: unit + compile regression check
- review pass 2: manual CLI smoke test and benchmark-export inspection
- review pass 3: diff/docs consistency check
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- primary implementation commit: `f379710cdbf32c83f068a81c7e3311cfb23e71e6`

## Next step
- add optional literal normalization so numeric constants can be bucketed for more aggressive code-clone demos without rewriting the rest of the MinHash pipeline
