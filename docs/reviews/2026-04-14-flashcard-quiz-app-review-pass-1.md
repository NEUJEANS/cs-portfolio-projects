# Flashcard Quiz App Review Pass 1

## Focus
CLI/API surface for the new recommendation feature.

## Findings
1. Added `--show-recommendations` but needed explicit validation for `--recommend-limit` and for missing `--history-path`.
2. The first draft used a generic error message that was misleading when only one history-output flag was set.

## Fixes Applied
- added `--recommend-limit` positive-integer validation
- made missing-history error messages flag-specific
- re-ran the unit suite after the parser changes
