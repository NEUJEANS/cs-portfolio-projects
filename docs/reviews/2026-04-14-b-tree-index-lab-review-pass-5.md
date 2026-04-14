# Review pass 5 — b-tree-index-lab deletion slice

## Focus
Test coverage and edge cases.

## Checks
- added regression tests for deleting a leaf key, deleting an internal key, deleting a missing key, and repeated deletions that collapse height
- added CLI delete command test to confirm scripting/demo output
- confirmed legacy insert/search/range tests still represent the original slice

## Fixes made
- expanded automated tests so the new vertical slice is demonstrated end-to-end
