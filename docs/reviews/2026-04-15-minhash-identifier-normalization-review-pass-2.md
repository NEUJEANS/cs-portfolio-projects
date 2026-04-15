# Review pass 2 — MinHash identifier normalization

Focus: manual CLI behavior and portfolio usefulness.

## Checks run
- `tmpdir=$(mktemp -d) && cat > "$tmpdir/a.py" <<'PY' ... && python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare "$tmpdir/a.py" "$tmpdir/b.py" --token-mode code --normalize-identifiers --shingle-size 3 --json`
- `python3 projects/minhash-near-duplicate-lab/minhash_lab.py build-index "$tmpdir" "$tmpdir/index.json" --glob '*.py' --token-mode code --normalize-identifiers --shingle-size 3 --json`
- `python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark "$tmpdir" --glob '*.py' --token-mode code --normalize-identifiers --shingle-size 3 --output "$tmpdir/bench.md" --json`

## Finding
- The CLI now exposes normalization cleanly across compare/build-index/benchmark flows, and the Markdown benchmark export makes the normalization choice visible for portfolio screenshots.

## Outcome
- No code changes were needed after the manual smoke test.
