# Wrap-up — 2026-04-16 01:36 UTC

## What changed
- added a `write-preset` CLI command for the MinHash lab with a curated `mixed-markdown-code-notebook` corpus
- added comma-separated glob support so mixed Markdown, Python, and notebook files can be scanned/indexed together
- refreshed the MinHash README, checklist, and review notes for the new demo workflow
- expanded the test suite with preset generation, overwrite safety, glob parsing, and end-to-end mixed-corpus CLI coverage

## Tests and reviews run
- `python3 -m unittest tests.test_minhash_near_duplicate`
- manual CLI self-test: `write-preset` + `corpus --glob '*.md,*.py,*.ipynb' --token-mode code --normalize-identifiers --normalize-literals --shingle-size 4 --threshold 0.2`
- review pass 1: corrected stale `--normalize-literals` help text
- review pass 2: added overwrite-safety regression coverage for preset writes
- review pass 3: added end-to-end CLI regression coverage for mixed-language scans
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- implementation commit: `9966d1c5c109a4a062dc0d1bd66bcaa7de595315`

## Next step
- add the planned dry-run corpus diff summary before `refresh-index` so large saved indexes can be previewed safely before recomputation
