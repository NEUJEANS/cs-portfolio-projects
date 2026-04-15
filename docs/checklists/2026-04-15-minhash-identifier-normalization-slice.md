# 2026-04-15 MinHash identifier-normalization slice

- [x] sync local branch with GitHub before edits
- [x] choose the MinHash code-clone follow-up around identifier normalization
- [x] refresh Python keyword/tokenization rules and self-test the intended API shape
- [x] implement `--normalize-identifiers` for `compare`, `corpus`, `build-index`, and `benchmark` when `--token-mode code` is active
- [x] persist normalization metadata in saved indexes so refresh/scan remain resumable
- [x] expand automated tests for normalized code tokens, similarity deltas, CLI validation, benchmark exports, and saved-index round-trips
- [x] update README and project checklist notes
- [x] complete 3 review passes and fix findings
- [x] run project tests and manual CLI smoke tests
- [x] run secret scan before push
- [x] commit, push, and log wrap-up
