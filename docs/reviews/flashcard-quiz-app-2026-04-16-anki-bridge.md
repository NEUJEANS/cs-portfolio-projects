# Flashcard Quiz App Review Log — 2026-04-16 Anki bridge slice

## Review pass 1 — automated correctness
- Ran `python3 -m unittest discover -s . -p 'test_*.py'` in `projects/flashcard-quiz-app`.
- Added regression coverage for TSV/TXT imports, bridge bundle export/import, and malformed package handling.
- Fix applied: normalized the missing-entry error so broken bridge zips fail with a clear required-file message.

## Review pass 2 — runtime smoke
- Ran `python3 -m py_compile flashcards.py test_flashcards.py`.
- Ran a CSV -> Anki text + bridge zip export smoke test.
- Loaded the generated `.anki.zip` bundle back through `load_cards()` to verify round-trip behavior.
- Confirmed the CLI emits clear export messages and the bundle stays dependency-free.

## Review pass 3 — docs/portfolio audit
- Updated the project README with the new deck formats, bridge caveat, and CLI examples.
- Marked the long-term flashcard checklist item complete and added a resumable slice checklist plus learning note.
- Confirmed the slice now reads like a coherent portfolio story: core quiz app + history + recommendations + interoperability bridge.
