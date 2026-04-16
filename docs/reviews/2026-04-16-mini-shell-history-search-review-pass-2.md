# Mini Shell History Search Review — Pass 2

## Findings
1. Failed history searches should not leave behind raw designators such as `!git` in the stored history.
2. The implementation already expanded before appending, but that contract was not protected by a direct test.

## Fixes applied
- added a regression test that verifies an unmatched search raises an error without mutating the history list

## Result
Search failures now stay clean and predictable for both users and future maintainers.
