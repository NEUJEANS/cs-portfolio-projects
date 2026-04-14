# Review pass 2 - minhash persistence slice

## Checked
- manual CLI runs for `build-index`, `scan-index`, and `benchmark`
- whether benchmark output stayed honest on a tiny corpus where LSH can miss true matches
- JSON payload clarity for portfolio/demo use

## Issue found
- benchmark output used a misleading `reported_pairs` field that looked like a correctness failure when LSH produced zero candidates on tiny corpora.

## Fix applied
- replaced the ambiguous field with `exact_pairs_above_threshold`, `lsh_pairs_above_threshold`, and `lsh_recall_vs_exact`.
