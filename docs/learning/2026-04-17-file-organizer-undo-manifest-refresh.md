# Node CLI refresh — file-organizer undo manifests — 2026-04-17

## Refreshed concepts
- A rollback manifest should store the exact realized destination paths, not just intended ones, because organize-time collisions can change the final filename.
- Undo should replay moves in reverse order so cleanup of empty generated directories stays correct.
- Restore paths need the same collision handling as forward organize paths; otherwise an undo could overwrite newer user files.
- `node:test` is enough to cover organize + undo flows, including dry-run preview behavior and cleanup edge cases.

## Quick self-test
- Could I explain why a dry-run manifest must not be undoable? Yes — no real file moves happened, so the manifest is only a preview.
- Could I describe why reverse-order restore matters? Yes — it avoids deleting a bucket directory before later manifest entries still need it.
- Could I test a restore collision cleanly? Yes — organize a file, create a new file at the original location, then verify undo restores into a numbered fallback path.
- Could I explain the difference between an audit manifest and a signed/tamper-evident manifest? Yes — this slice adds auditability first, not cryptographic integrity.
