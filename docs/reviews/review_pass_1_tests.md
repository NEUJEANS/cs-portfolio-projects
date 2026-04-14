# Review Pass 1 - Automated Tests

Date: 2026-03-27 UTC

## What was checked
- Python unit tests for all 12 Python projects
- Node tests for all 3 Node projects

## Findings
- Initial failure in `flashcard-quiz-app/test_flashcards.py` due to an unterminated multiline string literal.
- Initial Node discovery gap: test filenames were not in `node --test` discovery format.
- Initial `static-site-generator` test/code escaping issue from generated newline/regex literals.

## Fixes applied
- corrected CSV fixture string escaping in flashcard test
- renamed Node tests to `*.test.js`
- rewrote `sitegen.js` and `sitegen.test.js` with correct escaping

## Result
- all project tests passing
