# Review pass 3 — MinHash identifier normalization

Focus: docs consistency and final diff hygiene.

## Checks run
- `git diff --check`
- `git diff -- projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py projects/minhash-near-duplicate-lab/README.md docs/checklists/minhash-near-duplicate-lab.md docs/checklists/2026-04-15-minhash-identifier-normalization-slice.md docs/learning/2026-04-15-minhash-identifier-normalization-refresh.md docs/reviews/2026-04-15-minhash-identifier-normalization-review-pass-1.md docs/reviews/2026-04-15-minhash-identifier-normalization-review-pass-2.md docs/reviews/2026-04-15-minhash-identifier-normalization-review-pass-3.md`

## Finding
- README examples, JSON snippets, checklist notes, and saved-index metadata all describe the same `--normalize-identifiers` behavior.

## Outcome
- Final diff is consistent and ready for secret scan + commit.
