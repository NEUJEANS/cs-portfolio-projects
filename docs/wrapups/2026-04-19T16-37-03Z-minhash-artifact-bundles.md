# MinHash preset artifact bundles slice — 2026-04-19T16:37:03Z

## What changed
- fetched `origin`, confirmed local `main` had no remote drift before editing, then resumed the unfinished `minhash-near-duplicate-lab` artifact-bundle slice
- added preset artifact bundle generation to `minhash_lab.py` so curated preset corpora can emit JSON, Markdown, and HTML portfolio artifacts in one CLI run
- hardened bundle generation so it only analyzes the files written for the current preset run and so notebook previews work with both list- and string-based cell sources
- updated `projects/minhash-near-duplicate-lab/CHECKLIST.md` and `README.md` to document the completed slice and clarify that `--artifact-bundle-dir` works across all curated presets
- expanded `tests/test_minhash_near_duplicate.py` with artifact-bundle coverage, stray-file isolation coverage, notebook-preview coverage, and CLI end-to-end bundle assertions
- generated and committed a sample web-dev artifact bundle under `docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/`
- recorded the 3-pass review log in `docs/reviews/2026-04-19-minhash-artifact-bundle-review.md`

## Research / refresh
- no external web research was needed; this slice stayed inside the existing MinHash/LSH preset-generation architecture
- no separate language refresh was needed beyond validating the new Python bundle helpers through tests and CLI smoke runs

## Tests and validation run
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py` (`53 passed`)
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset web-dev-component-clones docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/preset --artifact-bundle-dir docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/bundle --json`
- `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py corpus docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones/preset --glob '*.md,*.tsx,*.ts,*.css' --token-mode code --normalize-identifiers --normalize-literals --shingle-size 4 --threshold 0.15 --json`
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Reviews run
- pass 1: bundle isolation audit; fixed destination re-scan contamination risk from stray matching files
- pass 2: notebook preview robustness audit; fixed string-based notebook cell handling
- pass 3: docs/operator UX audit; clarified README coverage for artifact bundles across all presets
- detailed review log: `docs/reviews/2026-04-19-minhash-artifact-bundle-review.md`

## Feature commit
- `a3217872e6f4b2c359cb196fe6f25ed53c81ae53`

## Next step
- add a cross-preset landing page that compares the mixed-language, data-science, systems, and web-dev demo bundles side by side
