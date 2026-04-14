# autocomplete-trie-cli review pass 1

## Focus
CLI and input validation audit.

## Issues found
1. Query strings were not normalized or validated, so empty/invalid input could flow into search logic.
2. CLI-side fuzzy de-duplication rebuilt the prefix word set inline instead of once.

## Fixes applied
- added `normalize_query()` with trim/lower/alpha checks
- validated query during CLI execution and surface errors as dataset-style input errors
- computed `prefix_words` once before filtering fuzzy matches
