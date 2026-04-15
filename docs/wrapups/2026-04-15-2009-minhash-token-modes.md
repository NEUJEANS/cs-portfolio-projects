# Wrap-up — 2026-04-15 20:09 UTC

## What changed
- added `word`, `code`, and `char` token modes to the MinHash near-duplicate lab
- persisted `token_mode` metadata in signature indexes so `build-index`, `scan-index`, and `refresh-index` stay compatible and resumable
- expanded CLI/benchmark payloads and exports to surface token-mode selection
- added tests for tokenizer modes, code-mode comparisons, index round-trips, and benchmark/export metadata
- updated the project README and checklists for the new slice

## Tests and reviews run
- `python3 -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `python3 -m unittest tests.test_minhash_near_duplicate`
- `python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare projects/minhash-near-duplicate-lab/minhash_lab.py projects/minhash-near-duplicate-lab/minhash_lab.py --token-mode code --shingle-size 4 --json`
- review pass 1: unit + CLI coverage run
- review pass 2: syntax compile + code-mode self-check
- review pass 3: manual git diff inspection of code, docs, and checklist changes

## Commit hash
- implementation commit: `b1208ca23d7cec7df87b4f60bf3fce095d030831`

## Next step
- add optional identifier normalization in `code` mode so variable renames can be collapsed more aggressively during source-code near-duplicate demos
