# deadlock-detector-lab dashboard delta-panel wrap-up

- Timestamp: `2026-04-22T02:00:43Z`
- Feature commit: `571b09e`

## What changed
- added an optional `--banker-contrast-input` to the `dashboard` command so the main detection-vs-avoidance report can compare one granted and one denied Banker request in the same artifact
- extended the dashboard JSON model with `banker_request_contrast` and `banker_request_delta_callout` so the comparison stays machine-readable
- added a new dashboard Markdown and HTML section that summarizes shared slack spent, granted-only and denied-only slack differences, first runnable-set changes, lost runnable options, and denied-path blocking
- added a CLI guardrail that rejects `--banker-contrast-input` unless `--banker-request-input` is also present
- refreshed the deadlock-detector checklist, README, research note, self-test, review log, and committed sample dashboard artifacts under `docs/artifacts/deadlock-detector-lab/`

## Tests and reviews run
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py` (`19/19` passing)
- real dashboard smoke regeneration with contrast input plus a no-request fallback smoke
- deterministic rerun checks with `cmp` for dashboard Markdown, HTML, and JSON outputs
- `git diff --check`
- TruffleHog secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review log: `docs/reviews/2026-04-22-deadlock-detector-dashboard-delta-review.md`

## Next step
- add a multi-request dashboard mode that compares more than one risky Banker request pair in the same one-page report
