# autocomplete-trie-cli review pass 3

## Focus
Ranking correctness and edge-case coverage.

## Issues found
1. Duplicate words with different weights were handled sensibly in code but not protected by tests.
2. Regression risk was higher than necessary without an explicit assertion on highest-weight retention.

## Fixes applied
- added a test verifying duplicate words retain the highest observed weight in trie results
- reran the full project test suite after the additional coverage
