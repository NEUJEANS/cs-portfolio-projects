# Mini Shell History Review — Pass 2

## Findings
1. Empty-history replay was covered, but there was no direct regression test for out-of-range numbered lookups such as `!3` when only one command exists.
2. Without that test, a future refactor could accidentally blur the error path for invalid numbered recalls.

## Fixes applied
- added a focused unit test that verifies out-of-range numbered history references fail with `history entry not found: N`

## Result
Both major history replay failure modes are now pinned: empty-history `!!` and out-of-range `!N`.
