# WAL KV Store Review Pass 1

## Focus
Behavioral consistency and CLI ergonomics.

## Issues found
1. `delete` output did not say whether the key existed before writing a tombstone.
2. In-memory history after `checkpoint` kept pre-compaction mutations, while a reloaded process did not.

## Fixes applied
- Added `existed` to delete responses.
- Cleared active mutation history on checkpoint so live-process behavior matches reload behavior.
