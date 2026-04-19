# MinHash web-dev preset review log — 2026-04-19

## Pass 1 — preset realism audit
- reviewed the new preset corpus for portfolio/story accuracy
- issue found: the initial `dashboard_story.md` text mentioned shared empty-state structure, but the preset files only demonstrated shared KPI/card layout patterns
- fix: rewrote the note to describe KPI, delta, and card-layout overlap instead of claiming an empty-state flow that was not present

## Pass 2 — naming and fixture consistency audit
- reviewed generated file names and test expectations for frontend realism
- issue found: the first CSS fixture name used camelCase (`cardShell.css`), which is less idiomatic than a kebab-case asset name for frontend demo corpora
- fix: renamed the preset asset to `card-shell.css` and updated the fixture existence test accordingly

## Pass 3 — regression and guardrail audit
- reviewed whether the new tests would catch silent fixture drift
- issue found: the first web-dev preset tests only asserted minimum file counts, which could let accidental file loss slip through without failing CI
- fix: tightened the new web-dev tests to assert the exact `files_written == 8` contract while keeping the pair-count assertion tolerant enough for future tokenizer improvements

## Validation rerun after fixes
- `./.venv/bin/python -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`
- `./.venv/bin/python -m pytest -q tests/test_minhash_near_duplicate.py`
- smoke preset scan:
  - `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py write-preset web-dev-component-clones "$TMPDIR" --json`
  - `./.venv/bin/python projects/minhash-near-duplicate-lab/minhash_lab.py corpus "$TMPDIR" --glob '*.md,*.tsx,*.ts,*.css' --token-mode code --normalize-identifiers --normalize-literals --shingle-size 4 --threshold 0.15 --json`
- `git diff --check`
