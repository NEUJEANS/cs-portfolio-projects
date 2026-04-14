# Library Manager Review Pass 2 — 2026-04-14

## Focus
Validation and compatibility.

## Issues found
- blank title/author values could still be inserted after stripping
- upgraded schemas needed explicit migration coverage so older databases would not silently miss new columns

## Fix applied
- added validation for empty title/author input
- added a migration regression test that creates an old-style table and verifies the new columns are added automatically

## Result
The upgrade is safer for both new and pre-existing SQLite databases.
