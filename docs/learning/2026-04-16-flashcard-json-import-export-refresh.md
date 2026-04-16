# Flashcard Quiz App JSON import/export refresh

## Quick refresh
- Python's `json` module is enough for a portfolio-friendly normalized deck format; no extra dependency is needed.
- A practical normalized shape is either a top-level list of cards or an object wrapper with `cards`, which makes room for metadata like export timestamps and versioning.
- For compatibility, tag parsing should accept both comma-separated strings and explicit JSON arrays, then normalize to a stable lowercase tuple inside the app.
- Export should preserve a deterministic schema so the generated file is easy to diff and easy to re-import.

## Tiny self-test
- Confirmed the chosen schema can round-trip through `json.dumps` / `json.loads` with nested `cards` metadata and array tags.
- Confirmed validation should fail fast when JSON cards are not objects or when prompt/answer fields are blank.

## Slice decision
Implement JSON deck import plus normalized JSON export now; defer true Anki package support because `.apkg`/collection packaging is a bigger interoperability slice than this run needs.
