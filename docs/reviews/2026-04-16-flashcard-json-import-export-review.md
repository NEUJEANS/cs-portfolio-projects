# Review — flashcard JSON import/export slice

## Pass 1 — CLI/API shape
- Checked that existing CSV usage still works while broadening the positional input from CSV-only to deck files.
- Verified the slice stayed interview-friendly: normalized JSON import/export rather than a half-finished Anki package writer.
- Issue found: docs still described the project as CSV-only.
- Fix applied: updated README overview, deck format docs, usage examples, and future-improvement wording.

## Pass 2 — validation and data-shape safety
- Checked JSON parsing and schema handling for list payloads, object payloads, bad card entries, blank prompt/answer fields, and mixed tag shapes.
- Issue found: JSON tags needed to accept both string and array forms to keep exported decks easy to re-import and hand-edit.
- Fix applied: generalized `parse_tags()` and added tests for list + string JSON tag inputs and invalid card entries.

## Pass 3 — conversion workflow and regression safety
- Ran unit tests, bytecode compilation, and an export-only smoke test to verify the non-interactive conversion path.
- Checked that export output is deterministic enough for diffs (`sort_keys=True`, stable card schema) and preserves tag ordering.
- Issue found: none after the smoke test; kept the slice as-is.
