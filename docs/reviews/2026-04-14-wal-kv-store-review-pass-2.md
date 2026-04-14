# WAL KV Store Review Pass 2

## Focus
Recovery semantics and documentation accuracy.

## Issues found
1. README needed to explain that checkpointing compacts away prior mutation history.
2. Root project index did not yet list the new project.

## Fixes applied
- Updated project README feature notes to clarify delete/checkpoint behavior.
- Added `wal-kv-store` to the repository root README project list.
