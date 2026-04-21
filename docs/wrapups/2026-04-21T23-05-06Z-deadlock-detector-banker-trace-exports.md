# Deadlock detector Banker trace/export slice — 2026-04-21T23:05:06Z

## What changed
- safely fetched and verified `main` against `origin/main` before editing, then took the next deadlock-detector follow-up promised in the prior Banker's wrap-up
- extended `projects/deadlock-detector-lab/deadlock_detector.py` so Banker's safety analysis now records step-by-step `trace_steps` with runnable sets, `work` vectors, released allocations, and blocking shortages for stalled unsafe states
- extended `request-banker` so trial request evaluation keeps separate hypothetical `trial_*` state plus trace/blocking details for explainable safe or denied outcomes
- added `--markdown-out` support for `analyze-banker` and `request-banker`, then committed sample Markdown and JSON artifacts under `docs/artifacts/deadlock-detector-lab/`
- refreshed the project README plus checklist, research note, learning self-test, and review log so the slice is resumable

## Tests and validation run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`13/13`)
- `python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-banker projects/deadlock-detector-lab/sample_banker_state.json --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_trace.md`
- `python3 projects/deadlock-detector-lab/deadlock_detector.py request-banker projects/deadlock-detector-lab/sample_banker_request.json --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_request_trace.md`
- deterministic double-run `cmp` checks for both Banker's JSON and Markdown trace exports
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git file:///home/user1_admin/.openclaw/workspace/cs-portfolio-projects --results=verified,unknown --fail`

## Reviews run
- pass 1: safety-sequence compatibility audit, fixed trace instrumentation so it preserves the old deterministic Banker's sample sequence instead of changing the finish order
- pass 2: denied-request trace audit, fixed the request result model so denied requests keep live state separate from hypothetical `trial_*` state while still exposing blocking shortages
- pass 3: docs and artifact audit, fixed the README/examples to cover both new `--markdown-out` flows and committed the sample export artifacts
- detailed review log: `docs/reviews/2026-04-21-deadlock-detector-banker-trace-export-review.md`

## Feature commit
- `f3e7c7f94cc1a0755083830585b1f8a4bc099ae5`

## Next step
- add Graphviz `.dot` or SVG wait-for/resource-allocation visuals so detection and avoidance demos can share one visual storytelling layer
