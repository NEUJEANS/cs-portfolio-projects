# MinHash token modes slice checklist

- [x] verify repo sync status before edits
- [x] do brief research on character shingles and code-token shingles for MinHash-style dedup
- [x] refresh tokenizer/shingling implementation details and validate a small API sketch
- [x] add CLI-selectable `word`, `code`, and `char` token modes
- [x] persist token-mode metadata in signature indexes so scan/refresh reuse the correct representation
- [x] expand automated tests for new modes, index round-trip behavior, and export metadata
- [x] run at least 3 review passes and fix issues found
- [x] commit, push, and append wrap-up
