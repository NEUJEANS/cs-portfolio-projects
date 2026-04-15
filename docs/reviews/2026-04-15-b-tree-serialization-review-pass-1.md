# 2026-04-15 B-tree serialization review pass 1

## Focus
Manual code review of serialization/deserialization paths and CLI ergonomics.

## Issue found
- `save PATH` wrote directly to the target file but did not create parent directories, so nested output paths like `artifacts/btree/tree.json` would fail during demos.

## Fix
- Updated `BTreeIndex.save()` to create parent directories with `mkdir(parents=True, exist_ok=True)` before writing the JSON snapshot.

## Result
- Nested save destinations now work in one command, which makes the persistence workflow more robust and easier to demo.
