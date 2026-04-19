# MinHash near-duplicate lab web-dev preset slice — 2026-04-19T16:14:31Z

## What changed
- safely fetched `origin`, confirmed local `main` matched `origin/main`, and selected `minhash-near-duplicate-lab` as a strong unfinished project because it still lacked a frontend-focused preset family
- added a new `web-dev-component-clones` preset corpus to `minhash_lab.py` so the project can demo near-duplicate React-style dashboard cards, hooks, notes, and CSS assets
- added `projects/minhash-near-duplicate-lab/CHECKLIST.md` to make future vertical slices resumable
- updated the MinHash README with the new preset, mixed-extension corpus-scan example, and refreshed future-improvement notes
- expanded `tests/test_minhash_near_duplicate.py` with preset-generation and end-to-end CLI corpus-scan coverage for the new frontend corpus
- recorded the 3-pass review/fix log in `docs/reviews/2026-04-19-minhash-web-dev-preset-review.md`

## Research / refresh
- no external web research was needed for this slice because the change stayed within the existing MinHash/LSH preset-generation framework already established in the repo
- no separate language refresh was needed beyond validating the TypeScript/TSX fixture style through the new CLI scan tests

## Tests and validation run
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py` (`48 passed`)
- preset smoke:
  - `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset web-dev-component-clones "$TMPDIR" --json`
  - `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py corpus "$TMPDIR" --glob '*.md,*.tsx,*.ts,*.css' --token-mode code --normalize-identifiers --normalize-literals --shingle-size 4 --threshold 0.15 --json`
- `git diff --check`

## Reviews run
- pass 1: preset realism audit; fixed an overstated `dashboard_story.md` description so it matches the actual KPI/card-layout overlap in the fixtures
- pass 2: naming/fixture consistency audit; renamed `cardShell.css` to the more frontend-idiomatic `card-shell.css`
- pass 3: regression/guardrail audit; tightened the new web-dev preset tests to assert the exact generated file count instead of only a minimum
- detailed review log: `docs/reviews/2026-04-19-minhash-web-dev-preset-review.md`

## Feature commit
- `c25e14fc9a7ded30e3eae14eb50ad6e2aa6b0fb6`

## Next step
- add artifact-ready preset bundle export so the MinHash lab can generate screenshot-friendly markdown/gallery cards next to each curated demo corpus
