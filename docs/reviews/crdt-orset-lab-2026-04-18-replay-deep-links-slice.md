# CRDT OR-Set Lab — replay deep links review log (2026-04-18)

## Review pass 1 — code path / hash wiring
- Checked the `build_replay_frames(...)` diff to confirm sync checkpoints are numbered only on sync ops.
- Checked replay rendering logic for `#step-N` + `#sync-N` parsing and canonical hash updates.
- Result: no code issues left after escaping the regex backslashes used inside the generated JS.

## Review pass 2 — artifact/doc consistency
- Verified both committed replay artifacts contain the deep-link UI and `hashchange` handler.
- Verified README language and checklist notes mention `#step-N` / `#sync-N` usage.
- Result: docs and generated outputs match the implementation.

## Review pass 3 — real smoke test
- Served the repo locally with `python3 -m http.server 8765`.
- Opened `docs/artifacts/crdt-orset-lab/sample-ops-replay.html` in a browser.
- Confirmed the page renders the deep-link section and sync checkpoint link list.
- Navigated directly to `#sync-2` and confirmed the replay opened on step 5 with the expected sync details and highlighted current checkpoint.
- Issue found during the browser pass: on sync frames the “Current frame” link duplicated the stable sync link instead of also exposing the exact `#step-N` URL.
- Fix applied: the deep-link panel now shows `Exact frame` as the precise `#step-N` URL and keeps `Stable sync checkpoint` as the demo-friendly `#sync-N` URL.
- Post-fix browser re-open confirmed `#sync-2` lands on step 5 while the panel exposes both `#step-5` and `#sync-2`.
