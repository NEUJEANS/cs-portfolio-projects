# deadlock-detector-lab Banker request gallery wrap-up

- Timestamp: `2026-04-22T01:04:43Z`
- Feature commit: `70f213d`

## What changed
- added a new `compare-banker-requests` CLI command that compares multiple Banker request trials side by side and exports recruiter-friendly Markdown and HTML gallery artifacts
- promoted the previously test-only unsafe Banker request into a committed sample input at `projects/deadlock-detector-lab/sample_banker_request_unsafe.json`
- committed a deterministic unsafe request trace artifact set plus a new granted-vs-denied request gallery under `docs/artifacts/deadlock-detector-lab/`
- refreshed the README, checklist, research note, learning self-test, and review log for the new gallery workflow
- extended the test suite to cover the gallery CLI path

## Tests and reviews run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`18/18` passing)
- real artifact-generation smoke runs for:
  - `request-banker sample_banker_request_unsafe.json`
  - `compare-banker-requests sample_banker_request.json sample_banker_request_unsafe.json`
- deterministic rerun checks with `cmp` for unsafe trace Markdown/SVG/HTML/JSON and gallery Markdown/HTML/JSON
- `git diff --check`
- TruffleHog secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git file:///home/user1_admin/.openclaw/workspace/cs-portfolio-projects --results=verified,unknown --fail`
- review log: `docs/reviews/2026-04-22-deadlock-detector-request-gallery-review.md`

## Next step
- add a compact delta-focused callout that highlights which resource slack and runnable-set options disappear between the granted and denied request paths
