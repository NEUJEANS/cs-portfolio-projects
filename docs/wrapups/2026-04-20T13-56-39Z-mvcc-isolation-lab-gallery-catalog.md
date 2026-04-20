# MVCC isolation lab wrap-up — 2026-04-20T13:56:39Z

## What changed
- safely sync-checked `main` against `origin/main` before editing (`ahead/behind 0/0`) and resumed the existing unfinished MVCC gallery/catalog slice instead of starting a new project
- added a first-class `catalog` CLI command to `projects/mvcc-isolation-lab/mvcc_isolation_lab.py` that discovers the committed scenario JSON files, regenerates each scenario's Markdown compare report + HTML dashboard + SVG timelines, and writes a single landing-page bundle
- committed the new static landing-page artifacts at `docs/artifacts/mvcc-isolation-lab/index.html` and `docs/artifacts/mvcc-isolation-lab/index.md`
- refreshed `projects/mvcc-isolation-lab/README.md`, the project/root checklist files, and added slice-specific checklist + 3-pass review notes
- during review, improved the landing page by surfacing per-scenario anomaly counts in the HTML cards and adding a regenerate hint to the Markdown landing page

## Tests and reviews run
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v` (`29/29`)
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py catalog projects/mvcc-isolation-lab --output-dir docs/artifacts/mvcc-isolation-lab`
- deterministic double-export hash check for `docs/artifacts/mvcc-isolation-lab/index.html` and `docs/artifacts/mvcc-isolation-lab/index.md`
- `git diff --check`
- review log: `docs/reviews/mvcc-isolation-lab-2026-04-20-gallery-catalog.md`
- pre-push secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Feature commit
- `da2ea5d6031fe86b70a57c6a572dd5cc595f018b` — `feat(mvcc-isolation-lab): add scenario gallery catalog`

## Next step
- add lightweight per-scenario timeline thumbnails or key anomaly callouts to the gallery so the landing page previews each concurrency story before a recruiter opens the deeper dashboard
