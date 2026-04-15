# MinHash literal-normalization notes

## Goal
Make code-clone demos more compelling when two snippets only differ by numeric constants, such as threshold changes or retry limits.

## Quick notes
- In token-based clone detection, replacing numeric literals with a stable placeholder can raise overlap without rewriting the rest of the shingling or MinHash pipeline.
- This is most useful for Type-2 style clones where structure stays the same and only identifiers/constants change.
- It should stay opt-in because constants can be semantically meaningful and over-normalization can hide important differences.

## Implementation choice for this slice
- Restrict normalization to `code` token mode.
- Bucket integer literals matched by the existing code tokenizer into a single `<num>` token.
- Persist the setting in saved signature indexes so `refresh-index` and `scan-index` stay compatible and resumable.
