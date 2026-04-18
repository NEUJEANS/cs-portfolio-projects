# CRDT OR-Set Lab — replay export-affordances review log (2026-04-18)

## Review pass 1 — code path / generated-script review
- Reviewed the replay-action implementation for copy-link fallback behavior, blob-download wiring, and checkpoint SVG generation.
- Found and fixed two generated-JavaScript defects during review: a Python `\s` escape warning inside the embedded regex source and a newline-escaping bug that broke the generated replay script at runtime.
- Added a regression test that extracts the generated replay script and runs `node --check` so embedded-JS syntax breakage is caught automatically.
- Result: replay action code is now syntactically validated in tests instead of only string-checked.

## Review pass 2 — docs / artifact consistency
- Regenerated the committed replay artifacts for the baseline and comparison scenarios.
- Verified README and checklist notes mention the copy-link and checkpoint-SVG export affordances.
- Cleaned duplicate future-follow-up bullets that had accumulated in the project checklist and README.
- Result: docs and committed artifacts match the implementation.

## Review pass 3 — real browser smoke test
- Served the repo locally with `python3 -m http.server 8765`.
- Opened `http://127.0.0.1:8765/docs/artifacts/crdt-orset-lab/sample-ops-replay.html?v=3#sync-2` in a browser.
- Confirmed the page lands on step 5, shows the canonical `#sync-2` hash, and exposes both the exact `#step-5` link and the stable sync link.
- Triggered the copy-sync action and verified the action note reports `Copied stable sync link #2.`
- Triggered the SVG export action and verified the action note reports the downloaded filename `script-sample-ops-json-sync-2.svg`.
- Result: the replay page now works in a real browser for deep-link load, copy-link actions, and checkpoint SVG download.
