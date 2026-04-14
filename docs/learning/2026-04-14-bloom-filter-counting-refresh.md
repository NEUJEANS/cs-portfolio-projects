# Python refresh + self-test for counting Bloom filters — 2026-04-14

## Refresh points
- A counting Bloom filter replaces a packed bitset with per-slot counters.
- `remove()` should only decrement counters when every hashed slot is already non-zero.
- JSON serialization is fine for small portfolio artifacts, but counter arrays grow much faster than bitsets.
- Overflow is a real API concern when counters are intentionally small.

## Self-test prompts
1. Why can't deletion work safely on a standard Bloom filter bitset?
2. What happens if two different items share some hashed slots and one is removed?
3. Why is explicit overflow handling better than silently capping counters?

## Short answers
1. Clearing a bit could break evidence needed by other items that hashed to the same slot.
2. Shared counters stay above zero as long as another item still contributes to them, so approximate membership still works.
3. Silent saturation hides data-quality problems and makes later removals unreliable to reason about.
