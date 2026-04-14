# Bloom Filter CLI Review Pass 1

## Focus
Counting-filter core behavior and serialization.

## Issues found
1. The project did not yet include a deletion-capable counting Bloom filter variant, so the portfolio story stopped at membership-only queries.
2. Serialized artifacts did not record a filter variant, which would make mixed standard/counting save files ambiguous.

## Fixes applied
- Added a `CountingBloomFilter` implementation with per-slot counters, `remove()` support, overflow checks, and counting-specific stats.
- Added `variant` metadata so saved JSON artifacts reload into the correct implementation.
- Expanded tests to cover counting-filter round trips, overflow handling, and removal behavior.
