# Wrap-up — 2026-04-15 20:47 UTC

## What changed
- added optional `--normalize-literals` support for MinHash `code` mode so numeric constants collapse into a stable `<num>` token during code-clone comparisons
- persisted literal-normalization metadata in saved signature indexes so `build-index`, `scan-index`, and `refresh-index` remain resumable and compatible
- extended benchmark/report payloads and Markdown/CSV exports to surface whether literal normalization was enabled
- expanded repository tests for numeric-token normalization, similarity deltas, CLI validation, export metadata, and saved-index round-trips
- updated the README, project checklist, research/learning notes, and 3 review logs for the new vertical slice

## Tests and reviews run
- `python3 -m unittest tests.test_minhash_near_duplicate`
- `python3 -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py`
- manual CLI smoke test covering `compare`, `build-index`, and `benchmark` with `--token-mode code --normalize-literals`
- `git diff --check`
- review pass 1: unit + compile regression check
- review pass 2: manual CLI smoke test and benchmark-export inspection
- review pass 3: diff/docs consistency check
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- primary implementation commit: `fa6fa98932d507753a4a633655cf8b8776032c1c`

## Next step
- add richer code-mode literal buckets for strings, booleans, and floating-point constants so clone-detection demos can compare normalization granularity instead of treating every non-integer literal the same way
