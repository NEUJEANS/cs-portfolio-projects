# Flashcard Quiz App Review Pass 1

## Focus
Data model and CSV parsing for tagged decks.

## Checks
- confirmed the optional `tags` column does not break old two-column decks
- confirmed tags are normalized to lowercase and deduplicated
- confirmed missing required fields still fail fast with a clear message

## Findings
No code changes required after this pass.
