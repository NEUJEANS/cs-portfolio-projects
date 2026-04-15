# LSM Tree Bloom Filter Refresh

Date: 2026-04-15

## Refreshed concepts
- Bloom filters allow false positives but not false negatives.
- Double hashing can derive multiple Bloom filter positions from one digest pair.
- In an LSM read path, Bloom filters are most valuable for negative lookups against many SSTables.
- Range metadata (`min_key`, `max_key`) is a cheap extra guard before a Bloom filter check.

## Self-test
1. **Why is a false negative unacceptable here?**
   Because the store would incorrectly skip an SSTable that really contains the key, returning a wrong miss.
2. **Why are false positives acceptable?**
   They only cause an unnecessary SSTable read, not a wrong result.
3. **Why add min/max key checks too?**
   They are deterministic, cheap, and can reject impossible lookups before any Bloom filter probe.
4. **Why keep Bloom metadata inside the SSTable JSON for now?**
   It keeps the project easy to inspect and explain during portfolio walkthroughs.
