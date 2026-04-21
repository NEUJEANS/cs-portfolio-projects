# MinHash benchmark pack slice — 2026-04-21T21:12:44Z

## What changed
- safely fetched `origin`, confirmed local `main` matched `origin/main`, and resumed the queued `minhash-near-duplicate-lab` follow-up around richer benchmark datasets
- added `write-benchmark-pack` to `projects/minhash-near-duplicate-lab/minhash_lab.py` so the repo can generate tiny, medium, and noisy benchmark corpora plus pack-level JSON, CSV, Markdown, and HTML summaries in one step
- encoded expected recall ranges for each scenario and exported checked-in benchmark artifacts under `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/`
- refreshed the project README, both long-running MinHash checklist files, a timestamped slice checklist, and a dedicated review log so the next follow-up stays resumable
- expanded `tests/test_minhash_near_duplicate.py` with benchmark-pack writer, force-safety, summary, and CLI coverage

## Research / refresh
- skipped external web research because this slice stayed inside the existing MinHash benchmark/export architecture
- self-tested the current benchmark API against draft tiny, medium, and noisy corpora before locking the scenario pack design

## Tests and validation run
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py` (`60 passed`)
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-benchmark-pack docs/artifacts/minhash-near-duplicate-lab/benchmark-pack --force --json`
- `git diff --check`
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-benchmark-pack --help`

## Reviews run
- pass 1: exact-pair ranking audit, fixed benchmark exact-match ordering so the strongest pair appears first in scenario summaries
- pass 2: CLI ergonomics audit, added destination help text for `write-benchmark-pack`
- pass 3: summary readability audit, normalized candidate-reduction formatting to four decimals in Markdown and HTML summaries
- detailed review log: `docs/reviews/2026-04-21-minhash-benchmark-pack-review.md`

## Feature commit
- `d241d6df39d3fd12c2418d837e772093d0c952e6`

## Next step
- add language-aware literal buckets for lists, dicts, template strings, and JSX inline objects in code mode
