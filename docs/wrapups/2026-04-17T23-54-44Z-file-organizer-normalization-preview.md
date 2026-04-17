# File organizer normalization preview slice

- **Timestamp:** 2026-04-17T23:54:44Z
- **Feature commit:** `90e373d9c91387f6c8a6c37f8598ef9c858ee225` (`feat(file-organizer-cli): add normalized-config preview mode`)
- **What changed:**
  - added `--preview-normalized-config <path>` so teams can inspect canonical shared-config rewrites before touching the file
  - preview mode now summarizes key cleanup actions such as removed unknown keys, normalized bucket/fallback names, extension cleanup, duplicate removal, canonical ordering, and default `extendDefaults` insertion when needed
  - added text/JSON reporting, CLI help/argument parsing, invalid-preview exit-code behavior, and README/checklist updates for the new review-first shared-config workflow
  - expanded tests to cover rewrite previews, already-canonical configs, text reporting, and the new CLI flag matrix
- **Tests / reviews run:**
  - safe-sync check before edit/push: local `main` matched `origin/main` at `e537a989ccddb966fdf6a01527d9c1d6400d3e27`
  - project tests: `npm test --prefix projects/file-organizer-cli` (`29/29` passing)
  - review pass 1: unit-suite review confirmed preview coverage for rewrite-heavy and already-canonical configs plus CLI/report formatting
  - review pass 2: preview smoke confirmed text + JSON preview output, verified the source config hash stayed unchanged after preview, and checked the canonical fallback/config payload in JSON output
  - review pass 3: invalid-preview + help smoke confirmed exit code `1` for broken configs and surfaced the new help entry; diff/docs audit then fixed roadmap/doc drift so README and CHECKLIST match the shipped CLI workflow
  - secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0` verified / `0` unknown)
- **Next step:** add small publishable demo artifacts that pair config-preview output with before/after folder-tree screenshots for the README and portfolio showcase.
