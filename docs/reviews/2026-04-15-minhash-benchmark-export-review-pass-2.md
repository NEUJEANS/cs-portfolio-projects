# Review pass 2 — MinHash benchmark export

Focus: manual CLI smoke test and portfolio usefulness.

## Checks run
- `tmpdir=$(mktemp -d) && printf 'alpha beta gamma delta epsilon zeta\n' > "$tmpdir/a.txt" && printf 'alpha beta gamma delta epsilon eta\n' > "$tmpdir/b.txt" && printf 'network routing consistent hashing replicas\n' > "$tmpdir/c.txt" && python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark "$tmpdir" --threshold 0.2 --output "$tmpdir/benchmark-summary.md" --json`
- `sed -n '1,120p' "$tmpdir/benchmark-summary.md"`

## Findings
- The CLI generated a Markdown report successfully and returned the saved path in JSON output.
- Manual smoke output showed an exact match above threshold even when LSH produced zero candidate pairs for that tiny sample. Keeping `top_exact_pairs` in the export makes that trade-off visible in portfolio write-ups.
- No further code change was needed because the new export already includes both `top_exact_pairs` and `top_lsh_pairs`.
