# Regex engine combined showcase wrap-up

- timestamp: `2026-04-19T19:20:43Z`
- project: `regex-engine-lab`
- feature commit: `58599ba` (`feat(regex-engine-lab): add combined showcase page`)
- sync status before edits: `main` vs `origin/main` was `ahead/behind 0/0` after `git fetch origin`

## What changed
- added `showcase-demo --html-out ... --artifact-dir ...` so the regex-engine project can generate a single static landing page over the committed trace and benchmark artifacts
- matched trace `pattern` + `mode` pairs against benchmark `case_definitions`, so each trace card now links directly to the dashboards that exercise the same regex case
- generated and committed `docs/artifacts/regex-engine-lab/showcase.html` as the browser-friendly hub that ties the low-level trace walk-throughs to the broader benchmark story
- refreshed README usage/examples plus checklist/research/learning/review notes so the showcase flow is discoverable and resumable in later cron runs

## Tests and review
- `python3 -m py_compile projects/regex-engine-lab/regex_engine_lab.py projects/regex-engine-lab/test_regex_engine_lab.py`
- `python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py'` → `40 tests`, `OK`
- `python3 projects/regex-engine-lab/regex_engine_lab.py showcase-demo --html-out docs/artifacts/regex-engine-lab/showcase.html --artifact-dir docs/artifacts/regex-engine-lab`
- `git diff --check`
- review passes logged in `docs/reviews/2026-04-19-regex-engine-showcase-review.md`
- TruffleHog scan clean before publish: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add a tiny AST/NFA explainer card that sits beside the trace and benchmark showcase page
