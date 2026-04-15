# 2026-04-15 B-tree serialization refresh and self-test

## Refresh
- `json.dumps(..., indent=2, sort_keys=True)` is enough for readable deterministic snapshots in a portfolio repo.
- `Path.write_text(...)` / `Path.read_text()` keeps the persistence path simple and cross-platform for small lab artifacts.
- Validation should happen after deserialization, not before, because decoded JSON can still violate tree invariants.

## Self-test
1. If a serialized internal node has 2 keys, how many children must it have?
   - 3 children.
2. Why validate `item_count` against the number of traversed items after loading?
   - To catch corrupted or hand-edited snapshots whose metadata no longer matches the actual tree contents.
3. Why keep `minimum_degree` in the snapshot?
   - Node capacity checks and future mutations depend on the same B-tree degree used when the tree was created.
