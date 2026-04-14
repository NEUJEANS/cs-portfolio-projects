# tfidf-search-lab review pass 1

## Focus
- indexing lifecycle and rebuild behavior
- correctness of candidate generation

## Findings
- Rebuilding the engine on the same instance would have retained previous postings and document-frequency state.

## Fixes made
- added `reset()` and call it at the start of `build_from_directory()`
- added a regression test covering rebuild/reset semantics
