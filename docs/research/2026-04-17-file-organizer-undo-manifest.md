# File Organizer undo-manifest slice research — 2026-04-17

## Goal
Upgrade `file-organizer-cli` from a one-way bulk organizer into a safer portfolio-grade tool that can record and reverse an organize run.

## Brief findings
- Node's `fsPromises.rename(oldPath, newPath)` is still the simplest primary move primitive; it fulfills with `undefined` on success and keeps the existing `EXDEV` fallback story relevant for cross-device moves.
- `fsPromises.mkdir(path, { recursive: true })` is enough to recreate parent folders during restore without pulling in extra dependencies.
- `fsPromises.access(path)` remains a straightforward existence check for collision-safe restore targets and missing-file detection during undo.
- For rollback flows, reversing the manifest order matters: the most recently organized file should be restored first so nested or shared bucket directories can be cleaned up safely after each restore.

## Sources checked
- Node.js `fsPromises.rename(...)` docs
- Node.js `fsPromises.mkdir(...)` docs
- Node.js `fsPromises.access(...)` docs

## Decisions for this slice
1. Add `--manifest-out <path>` so organize runs can persist a machine-readable manifest.
2. Add `--undo <manifest>` to restore files from a saved non-dry-run manifest.
3. Keep restore behavior collision-safe by reusing the numbered-suffix destination logic.
4. Remove now-empty bucket directories during undo, but never remove the project root.
5. Expand tests and README examples so the rollback workflow is easy to demo in interviews.
