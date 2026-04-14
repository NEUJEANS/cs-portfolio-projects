# Flashcard Quiz App Review Pass 2

## Focus
Recommendation quality and study-flow realism.

## Findings
1. Manual smoke testing showed that a card answered correctly once was still labeled `relearn now`, which was too aggressive.
2. The heuristic needed a clearer distinction between recent failures and low-exposure successes.

## Fixes Applied
- changed recommendation logic so recent misses or zero-correct low-exposure cards become `relearn now`
- moved first-time successes into `review soon`
- added a focused unit test for the single-success case
- repeated the smoke run to verify more intuitive output
