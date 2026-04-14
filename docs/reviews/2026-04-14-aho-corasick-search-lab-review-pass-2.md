# Review Pass 2 — Aho-Corasick Search Lab

## Checks
- audited README commands against the actual runtime environment
- smoke-tested CLI usage examples

## Issues found
- README used `pytest`, but the environment does not have pytest installed.
- README examples referenced generic files instead of repo-contained demo assets.

## Fixes applied
- changed the documented test command to `python3 projects/aho-corasick-search-lab/test_aho_corasick_search.py`.
- added `sample_patterns.txt` and `sample_text.txt` and updated README examples to use them.
