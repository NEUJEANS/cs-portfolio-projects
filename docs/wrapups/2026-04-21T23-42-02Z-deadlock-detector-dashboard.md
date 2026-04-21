# Deadlock detector detection-vs-avoidance dashboard slice — 2026-04-21T23:42:02Z

## What changed
- safely sync-checked tracked `main` against `origin/main` before editing (`ahead/behind 0/0`), then took the next deadlock-detector follow-up from the prior wrap-up: one combined detection-vs-avoidance dashboard
- extended `projects/deadlock-detector-lab/deadlock_detector.py` with a new `dashboard` command that combines the wait-for graph, resource-allocation snapshot, Banker's safety trace, and optional Banker's request trial into one report
- added deterministic Markdown, HTML, and JSON sample dashboard artifacts under `docs/artifacts/deadlock-detector-lab/`
- refreshed README usage, checklist, research notes, learning self-test, and a dedicated 3-pass review log so the slice stays resumable
- tightened the final dashboard after review with clearer per-panel `Question answered` framing, a more informative request takeaway, surfaced evaluated available-vector context, and optional-request CLI coverage

## Tests and validation run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`17/17`)
- `python3 projects/deadlock-detector-lab/deadlock_detector.py dashboard --wait-input projects/deadlock-detector-lab/sample_wait_graph.json --allocation-input projects/deadlock-detector-lab/sample_allocation_state.json --banker-input projects/deadlock-detector-lab/sample_banker_state.json --banker-request-input projects/deadlock-detector-lab/sample_banker_request.json --markdown-out docs/artifacts/deadlock-detector-lab/sample_detection_vs_avoidance_dashboard.md --html-out docs/artifacts/deadlock-detector-lab/sample_detection_vs_avoidance_dashboard.html > docs/artifacts/deadlock-detector-lab/sample_detection_vs_avoidance_dashboard.json`
- deterministic rerun `cmp` checks for the dashboard Markdown, HTML, and JSON artifacts
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Reviews run
- pass 1: narrative audit, fixed the request takeaway so it now includes the concrete request vector and resulting safe sequence instead of repeating the generic grant reason
- pass 2: comparison-framing audit, added explicit `Question answered` summaries to every panel so detection vs avoidance is legible in one glance
- pass 3: optional-path coverage audit, added regression coverage proving the dashboard still exports cleanly when the optional Banker's request input is omitted
- detailed review log: `docs/reviews/2026-04-21-deadlock-detector-dashboard-review.md`

## Feature commit
- `09b2999ad171bd9cc04afdb55043a113dfda7fa1`

## Next step
- add dedicated Banker's SVG or HTML visuals so the avoidance side gains the same at-a-glance diagram power as the wait-for and allocation panels
