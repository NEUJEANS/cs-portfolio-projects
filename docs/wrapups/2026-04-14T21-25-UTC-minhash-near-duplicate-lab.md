# Wrap-up — 2026-04-14 21:25 UTC

Project: `minhash-near-duplicate-lab`
Primary commit: `9d6dbba` (`Add minhash near-duplicate detection lab`)

## What changed
- created a new portfolio project for near-duplicate text detection using word shingles, exact Jaccard similarity, deterministic MinHash signatures, and LSH-style banding
- added a pairwise `compare` CLI mode and a corpus-scanning `corpus` mode with JSON output support
- added a small-corpus fallback so tiny demo datasets still surface similar pairs even when no band collisions occur
- added README guidance, research notes, refresh/self-test notes, project checklist, and 3 review logs
- updated repo-level project tracking to include the new lab

## Tests and reviews run
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- manual corpus JSON smoke test against temporary `.txt` files
- review pass 1: fixed small-corpus false-negative candidate generation
- review pass 2: aligned README with fallback behavior
- review pass 3: validated CLI input checks plus final test/docs consistency
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add persisted signature/index storage plus benchmarking so the lab can show repeated-scan performance trade-offs on larger corpora.
