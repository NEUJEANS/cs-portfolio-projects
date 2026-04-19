# Regex engine showcase AST/NFA explainer wrap-up

- timestamp: `2026-04-19T19:57:27Z`
- project: `regex-engine-lab`
- feature commit: `9b2c1d7` (`feat(regex-engine-lab): add showcase AST/NFA explainers`)
- sync status before edits: `main` vs `origin/main` was `ahead/behind 0/0` after `git fetch origin`

## What changed
- added AST/NFA explainer generation to `showcase-demo` by summarizing the existing `RegexEngine(...).explain()` payload for each committed trace example
- rendered compact explainer cards with AST story/shape, regex-feature counts, NFA shape metrics, and links to the related benchmark dashboards
- fixed review-found wording/robustness issues by handling irregular `class -> classes` pluralization and softening missing accept-state wording
- regenerated `docs/artifacts/regex-engine-lab/showcase.html` and refreshed README/checklist plus research/learning/review notes so the slice is resumable

## Tests and review
- `python3 -m py_compile projects/regex-engine-lab/regex_engine_lab.py projects/regex-engine-lab/test_regex_engine_lab.py`
- `python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py'` → `40 tests`, `OK`
- `python3 projects/regex-engine-lab/regex_engine_lab.py showcase-demo --html-out docs/artifacts/regex-engine-lab/showcase.html --artifact-dir docs/artifacts/regex-engine-lab`
- `git diff --check`
- review passes logged in `docs/reviews/2026-04-19-regex-engine-showcase-explainers-review.md`
- TruffleHog scan clean before publish: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add a trace-to-explainer SVG or HTML timeline card if the project needs a more visual walkthrough than raw JSON
