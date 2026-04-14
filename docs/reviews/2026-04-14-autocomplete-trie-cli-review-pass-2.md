# autocomplete-trie-cli review pass 2

## Focus
Dataset robustness and resumability.

## Issues found
1. Sample dictionaries could not include comment lines for annotation.
2. The test suite did not cover this small but useful loader behavior.

## Fixes applied
- loader now skips blank lines and `#` comment lines
- added test coverage for comment-line handling
