# File organizer shared-config lint slice

- **Timestamp:** 2026-04-17T23:23:54Z
- **Feature commit:** `1689eb5aa324bdf8b54443ce30e134a5c64e19c6` (`feat(file-organizer-cli): add shared-config lint mode`)
- **What changed:**
  - added `--lint-config <path>` so shared bucket JSON can be validated in CI or pre-commit without moving any files
  - strengthened config validation so invalid `extendDefaults` values and bucket-name collisions after normalization are rejected before organize runs
  - surfaced lint warnings for normalization drift (`CSV` -> `.csv`, trimmed bucket/fallback names), duplicate per-bucket extensions, and ignored unknown top-level keys
  - updated the project README and added `projects/file-organizer-cli/CHECKLIST.md` so the slice is resumable and demo-ready
- **Tests / reviews run:**
  - safe-sync check before edit/push: `main` matched `origin/main` at `f366738a9a4a8d94566f42b783c0b92c0e494d26`
  - project tests: `npm test --prefix projects/file-organizer-cli` (`25/25` passing)
  - real smoke: valid `--lint-config` text + JSON output, invalid lint exit-code failure, organize with the linted shared config, then manifest-based undo
  - review pass 1: regression audit caught a mismatched warning-count expectation in the new lint test; fixed the expectation and reran the suite
  - review pass 2: CLI/help + README/checklist audit confirmed the new lint mode is documented with CI-oriented examples and next-step tracking
  - review pass 3: diff/whitespace + end-to-end temp-directory smoke confirmed valid/invalid lint behavior and organize/undo reuse from a shared config
  - secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0` verified / `0` unknown)
- **Next step:** add an optional normalized-config writer (`--fix-config` / `--write-normalized-config`) so teams can auto-resolve lint warnings into canonical JSON before committing shared presets.
