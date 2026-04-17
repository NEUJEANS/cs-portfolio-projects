# File organizer normalized-config writers slice

- **Timestamp:** 2026-04-17T23:39:05Z
- **Feature commit:** `6e7791e0661ea345f2278c01b8bb2aad969ad806` (`feat(file-organizer-cli): add normalized shared-config writers`)
- **What changed:**
  - added in-place `--fix-config <path>` support so warning-heavy shared bucket configs can be rewritten into canonical JSON before teammates run organize
  - added exported `--write-normalized-config <source> <destination>` with `--force` overwrite protection for reviewable normalized-config outputs
  - normalized writer now trims bucket/fallback names, lowercases and dot-prefixes extensions, removes duplicate extensions, strips unknown top-level keys, and emits stable sorted bucket/extension ordering
  - extended CLI parsing/help text, text/JSON reporting, README usage/docs, and the project checklist so the new config-cleanup workflow is resumable
  - added regression coverage for copied and in-place normalization, invalid-config rejection, destination-clobber protection, parse-arg support, and text-report formatting
- **Tests / reviews run:**
  - safe-sync check before edit/push: local `main` matched `origin/main` at `2e0a8a82ef65defdf48394102cfa9ee00df787af`
  - project tests: `npm test --prefix projects/file-organizer-cli` (`27/27` passing)
  - review pass 1: lint + normalized-writer smoke (`--lint-config`, `--write-normalized-config`, `--fix-config`) confirmed canonical JSON output and warning resolution behavior
  - review pass 2: diff/docs audit caught two documentation drifts (normalized-output warning order and duplicated future-improvements wording); fixed both and reran tests
  - review pass 3: end-to-end organize/undo smoke with normalized config outside the target directory confirmed the intended workflow and led to an explicit README note about keeping raw helper artifacts outside the folder being organized
  - final smoke: `node organizer.js "$target" --config "$work/shared.json" --manifest-out "$work/manifest.json"` plus `node organizer.js --undo "$work/manifest.json"`
  - secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0` verified / `0` unknown)
- **Next step:** add a config-diff summary or autofix preview mode so teams can inspect normalization changes before writing them.
