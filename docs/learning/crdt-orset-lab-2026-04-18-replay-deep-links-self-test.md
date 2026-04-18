# CRDT OR-Set Lab — replay deep links self-test (2026-04-18)

## Refresh prompt
- What should a replay hash represent when the frame is a sync step?
- How do we avoid infinite re-render loops while still keeping the URL current during playback?
- Why keep both `#step-N` and `#sync-N` forms instead of only one?

## Answers
- Sync steps should expose a stable `#sync-N` checkpoint so demos stay shareable even if non-sync frames are added later.
- The renderer should update the URL with `history.replaceState(...)`; user-entered or clicked hashes should be handled through `hashchange`.
- `#step-N` is precise for any frame, while `#sync-N` is the easier classroom/demo handle for reconciliation moments.

## Implementation check
- Added `sync_checkpoint` metadata to replay frames.
- Added `indexFromHash(...)`, `hashForFrame(...)`, and `updateUrlHash(...)` to the replay page.
- Browser smoke test confirmed loading `#sync-2` lands on step 5 and highlights the current checkpoint.
