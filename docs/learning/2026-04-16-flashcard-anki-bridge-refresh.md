# Flashcard Quiz App — Anki bridge refresh

## Quick refresh
- Anki can import plain tab-separated text files where columns map cleanly to note fields such as Front, Back, and Tags.
- A dependency-free portfolio project does not need to generate Anki's full binary `.apkg` format to demonstrate interoperability; a portable bridge bundle with import-ready notes plus normalized JSON is often the safer standard-library slice.
- TSV is a good bridge format here because prompts/answers already fit naturally into fixed fields and tags can be serialized as a comma-separated third column.
- A small zip manifest makes the export resumable and self-describing while keeping future upgrades open.

## Self-test
- Can the loader round-trip cards through CSV -> bridge zip -> internal Card objects? Yes.
- Can the export stay useful even outside this project? Yes: `anki-notes.tsv` is directly importable into Anki and the bundle also preserves a normalized JSON deck.
- Biggest caveat: this is an Anki-friendly bridge, not a native `.apkg` generator.
