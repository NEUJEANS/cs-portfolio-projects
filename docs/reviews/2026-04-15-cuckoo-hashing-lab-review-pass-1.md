# 2026-04-15 Cuckoo hashing lab review pass 1

## Focus
Manual code review of insertion-cycle handling and rehash safety.

## Issue found
- A failed displacement chain could mutate the live table before rehashing, which meant some earlier entries could disappear when a cycle was hit.

## Fix
- Changed insert-time recovery to snapshot existing entries before a risky placement attempt and rebuild from the preserved entry list when a rehash is needed.

## Result
- Rehashing now preserves all previously inserted key/value pairs, including stress cases that force repeated cycles.
