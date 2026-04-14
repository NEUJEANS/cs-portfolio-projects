# Review pass 3 - minhash persistence slice

## Checked
- repository test coverage for new helpers and CLI commands
- index round-trip correctness and benchmark payload assertions
- README examples and test command accuracy

## Issue found
- the new slice needed explicit regression coverage for saved-index workflows and benchmark summaries.

## Fix applied
- expanded `tests/test_minhash_near_duplicate.py` with index round-trip tests plus CLI coverage for `build-index`, `scan-index`, and `benchmark`.
