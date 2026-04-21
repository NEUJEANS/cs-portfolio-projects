# Library manager SQLite review — 2026-04-21 — FTS search slice

## Pass 1 — test-intent review
- Re-read the new tests after the first green/failed run to make sure they expressed the intended distinction between substring search and ranked full-text search.
- Issue found: the keyword-mode test used `martin`, which correctly matched both `Robert C. Martin` and `Martin Fowler`, so the failure was in the test intent rather than the implementation.
- Fix: changed the keyword-mode assertion to query `robert` so it isolates substring behavior without overlapping author surnames.

## Pass 2 — forced-FTS error-path review
- Reviewed the failure behavior for `--search-mode fts` instead of only the happy path.
- Issue found: forced FTS mode collapsed two different cases into one vague message (`invalid or unsupported full-text query`), which would make CLI debugging harder.
- Fix: separated `LibraryError` handling from `sqlite3.OperationalError` so unsupported FTS builds now report `full-text search is not available...`, while malformed FTS syntax reports `invalid full-text query: ...`; added regression coverage for the unsupported-build branch.

## Pass 3 — docs/resumability review
- Reviewed the slice from the perspective of a future continuation run reading only the docs/checklist.
- Issue found: the README did not explicitly state that `--search-mode auto` falls back safely when FTS5 is unavailable, and the checklist did not yet record that the review trail exists.
- Fix: updated the project README with the fallback behavior and expanded the checklist so the review/logging work is visible for the next resumable slice.

## Final verification
- `python3 -m py_compile projects/library-manager-sqlite/library_manager.py projects/library-manager-sqlite/test_library_manager.py`
- `cd projects/library-manager-sqlite && python3 -m unittest -v test_library_manager.py` (`8/8`)
- real CLI smoke run for `add`, `list --search-mode auto`, and `list --search-mode keyword`
- `git diff --check`
