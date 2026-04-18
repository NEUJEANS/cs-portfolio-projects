# File organizer basename-pattern bucket rules slice

- **Timestamp:** 2026-04-18T00:27:29Z
- **Feature commit:** `6df5e0ea0b38f5037ecff524eaa97be40490b470` (`feat(file-organizer-cli): add basename pattern bucket rules`)
- **What changed:**
  - added richer shared-config bucket rules so custom buckets can use `basenamePatterns` with `*` / `?` wildcards in addition to plain extension arrays
  - organize runs now check basename-pattern matches before extension fallback, so files like `Screenshot 2026-04-18.png` or `quiz-2026-04-18.txt` can land in custom buckets even when their extensions normally map elsewhere
  - extended config linting, normalization previews, canonical config writing, and bucket-config reporting so object-style rule definitions stay reviewable and safe for team-shared JSON configs
  - expanded README + checklist coverage and added regression tests for wildcard matching, duplicate-pattern validation, lint normalization, and real organize moves with basename rules
- **Tests / reviews run:**
  - safe-sync check before edit: fetched `origin`, confirmed local `main` was ahead/behind `1/0` versus `origin/main` (local pending wrap-up only; no newer remote edits to overwrite)
  - project tests: `npm test --prefix projects/file-organizer-cli` (`34/34` passing)
  - review pass 1: unit tests caught the wildcard-regex translation bug for basename patterns; fixed the regex escaping/replacement path and tightened the single-character wildcard assertions
  - review pass 2: CLI preview + dry-run smoke on a temp folder/config verified normalized basename-pattern warnings plus dry-run bucket routing for screenshot/assignment-style filenames
  - review pass 3: real apply + undo smoke on a temp folder verified manifest-backed organize/restore behavior with basename-pattern buckets and triggered a final README/checklist audit to remove shipped-feature drift
- **Next step:** add MIME-aware detection rules so shared configs can distinguish files that share extensions but not content types.
