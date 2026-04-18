# file-organizer-cli — checksum-backed manifests

- **Timestamp:** 2026-04-18T06:14:09Z
- **Project:** `projects/file-organizer-cli`
- **Feature commit:** `f8cea61a29842bdfd2b531cd893f88d80eb2ec08` (`feat: add checksum-backed organizer manifests`)

## What changed
- added `--manifest-checksum` so organize runs can write SHA-256 integrity metadata into saved manifests
- added automatic manifest verification during `--undo`, plus explicit `--skip-manifest-verification` for manual recovery flows
- updated text reports so apply/undo output shows checksum and verification status
- expanded regression coverage for checksum writing, tamper detection, and CLI flag guards
- regenerated the committed demo bundle and refreshed README/checklist/review docs for the manifest-integrity workflow

## Tests and reviews run
- `npm test --prefix projects/file-organizer-cli`
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
- `git diff --check`
- real temp-dir smoke: organize with `--manifest-checksum`, tamper with the manifest, confirm normal undo fails closed, then confirm `--skip-manifest-verification` restores successfully
- review log: `docs/reviews/file-organizer-cli-2026-04-18-manifest-integrity.md` (3 review passes + validation rerun)
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add detached-signature support so teams can verify manifest authorship in addition to checksum integrity
