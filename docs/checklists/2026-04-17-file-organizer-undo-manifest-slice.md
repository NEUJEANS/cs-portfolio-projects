# File organizer undo-manifest slice (2026-04-17 22:07 UTC run)

- [x] confirm repo sync before editing
- [x] choose `file-organizer-cli` as the next weaker project slice
- [x] do brief Node fs research for manifest + restore semantics
- [x] do a short Node CLI / rollback self-test refresh
- [x] update checklist/docs so the slice is resumable
- [x] add manifest export support for organize runs
- [x] add `--undo <manifest>` restore support with reverse-order replay and collision-safe restores
- [x] clean up empty generated bucket directories after successful undo restores
- [x] expand tests for manifest writing, dry-run undo, restore collisions, and dry-run manifest rejection
- [x] refresh README examples and future-improvement notes
- [x] run targeted tests and CLI smoke checks
- [x] complete 3 review passes and fix issues found
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up

## Review notes
- review pass 1 should focus on manifest shape and CLI parsing edge cases.
- review pass 2 should focus on restore safety: reverse ordering, collision handling, and empty-directory cleanup.
- review pass 3 should focus on README/demo quality plus final runnable smoke tests.
