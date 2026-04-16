# Wrap-up — MinHash literal normalization slice

- Timestamp: 2026-04-16 01:24 UTC
- Project: `minhash-near-duplicate-lab`
- Main implementation commit: `354c256615c2b26beb8f5917ecc6350529e2ff4b`

## What changed
- expanded code-mode tokenization to preserve quoted strings and floating-point literals
- extended literal normalization to bucket integers, floats, strings, booleans, and `None`
- added a project checklist markdown file to track completed and remaining MinHash improvements
- updated README copy to document broader code-literal normalization behavior
- added regression tests for strings, booleans, `None`, floats, and scientific notation literals

## Tests and reviews run
- `python3 -m unittest tests.test_minhash_near_duplicate`
- CLI review: `python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare ... --token-mode code --normalize-literals --json`
- direct normalization review for `.5`, `1e6`, escaped strings, booleans, and `None`
- doc/checklist consistency review
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add mixed-language corpus presets or benchmark fixtures so the MinHash lab can demo clone detection across Markdown + code portfolios more convincingly
