# 2026-04-14 flashcard history slice

## Goal
Add a resumable portfolio-worthy upgrade to `flashcard-quiz-app` by persisting study outcomes across sessions.

## Notes
- Keep the implementation standard-library only so the project stays easy to run in interviews and classrooms.
- Use plain JSON for inspectable output instead of SQLite or a hidden binary format.
- Track aggregate performance per prompt so the app can surface historically weak cards without introducing scheduling complexity yet.
- Preserve the existing fast CLI path: history should be optional and should not block users who only want one-off quiz sessions.

## Scope for this run
- add `--history-path`
- save aggregate correct/incorrect counts per card prompt
- print a history summary when explicitly requested
- add tests for missing history, invalid JSON, and persisted summaries

## Deferred
- history migration/versioning beyond a basic `version` field
- import/export formats such as Anki or JSON deck conversion
- spaced repetition scheduling heuristics
