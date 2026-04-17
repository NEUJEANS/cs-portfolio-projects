# File organizer undo-manifest review — pass 1 — 2026-04-17

## Focus
Manifest shape and CLI parsing safety.

## Findings
- confirmed the manifest now captures the realized `to` paths, which is required for correct undo when organize-time collisions rename files
- found a CLI ambiguity: `--manifest-out` could still be combined with `--undo`, but the flag was ignored in undo mode instead of being rejected explicitly
- verified the dry-run manifest guard is necessary so preview-only manifests cannot be treated as real rollback plans

## Fixes made
- updated `parseArgs(...)` to reject `--manifest-out` when `--undo` is present
- extended the parse-args test to cover the new validation path

## Result
- CLI mode selection is now explicit instead of silently ignoring an invalid flag combination
