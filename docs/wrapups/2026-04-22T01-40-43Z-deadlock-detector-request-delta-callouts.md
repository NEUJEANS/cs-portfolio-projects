# deadlock-detector-lab request delta-callout wrap-up

- Timestamp: `2026-04-22T01:40:43Z`
- Feature commit: `c08f6eb`

## What changed
- added machine-readable `delta_callouts` to the Banker request gallery JSON so granted-vs-denied request comparisons explicitly report shared slack spent, granted-only slack spent, lost first runnable options, and denied-path blocking
- added a new Markdown and HTML `Delta callouts` section to the request gallery artifacts so the safe and unsafe request paths can be explained without mentally diffing the two cards
- reconstructed the pre-request available vector for granted requests before computing slack deltas so the comparison stays honest
- refreshed the deadlock-detector checklist, README, research note, self-test, and review log for the new delta-focused slice
- regenerated the committed request gallery artifact bundle under `docs/artifacts/deadlock-detector-lab/`

## Tests and reviews run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`18/18` passing)
- real gallery smoke regeneration:
  - `python3 projects/deadlock-detector-lab/deadlock_detector.py compare-banker-requests projects/deadlock-detector-lab/sample_banker_request.json projects/deadlock-detector-lab/sample_banker_request_unsafe.json --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.md --html-out docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.html > docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.json`
- deterministic rerun checks with `cmp` for gallery Markdown, HTML, and JSON outputs
- `git diff --check`
- TruffleHog secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review log: `docs/reviews/2026-04-22-deadlock-detector-request-delta-review.md`

## Next step
- pull the granted-vs-denied request delta callout into the main detection-vs-avoidance dashboard so the one-page portfolio story includes the new comparison insight too
