# File organizer custom-buckets slice (2026-04-17 22:30 UTC run)

- [x] confirm repo sync before editing
- [x] choose `file-organizer-cli` as the next resumable slice
- [x] do brief official-doc refresh for Node path/fs behavior
- [x] do a short Node CLI config/self-test refresh
- [x] update checklist/docs so the slice is resumable
- [x] add `--config <path>` support for config-driven custom buckets
- [x] support custom fallback bucket names and custom extension overrides
- [x] skip the active config file if it lives inside the directory being organized
- [x] expand tests for config parsing, custom fallback buckets, config-in-root safety, and CLI validation
- [x] refresh README examples and config docs
- [x] run targeted tests and runnable smoke checks
- [x] complete 3 review passes and fix issues found
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up

## Review notes
- review pass 1: config safety and recursive traversal behavior.
- review pass 2: CLI validation + regression coverage for new flag combinations.
- review pass 3: README/demo quality plus final organize/undo smoke with config inside the target root.
