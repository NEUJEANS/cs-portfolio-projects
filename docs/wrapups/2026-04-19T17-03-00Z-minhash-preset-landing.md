# MinHash preset landing page slice — 2026-04-19T17:03:00Z

## What changed
- safely fetched `origin`, confirmed local `main` had no remote drift before publishing, and resumed the unfinished `minhash-near-duplicate-lab` landing-page slice
- added `write-preset-landing` to `projects/minhash-near-duplicate-lab/minhash_lab.py` so checked-in preset bundle summaries can generate a shared Markdown/HTML/JSON landing page
- generated and committed the missing mixed-markdown, data-science, and systems preset bundles plus the shared landing outputs under `docs/artifacts/minhash-near-duplicate-lab/`
- updated the project README and both checklist files so the MinHash roadmap stays resumable
- recorded the 3-pass review log in `docs/reviews/2026-04-19-minhash-preset-landing-review.md`

## Research / refresh
- skipped external web research because this slice stayed inside the existing preset bundle/export architecture
- self-tested the aggregation/output path through new repo-level unit coverage and a real CLI smoke run

## Tests and validation run
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py` (`56 passed`)
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset-landing docs/artifacts/minhash-near-duplicate-lab docs/artifacts/minhash-near-duplicate-lab --json`
- `git diff --check`

## Reviews run
- pass 1: link-path robustness audit; replaced brittle relative-path logic with `os.path.relpath(...)`
- pass 2: CLI summary UX audit; bubbled total file/pair counts into the command result for automation
- pass 3: portfolio artifact completeness audit; generated and checked in the missing mixed/data-science/systems bundles before rebuilding the shared landing page
- detailed review log: `docs/reviews/2026-04-19-minhash-preset-landing-review.md`

## Feature commit
- `ce57347346d80519dc4ad228fc1e8a39560a20c5`

## Next step
- add richer benchmark dataset packs with expected-recall scenarios across tiny, medium, and noisy corpora
