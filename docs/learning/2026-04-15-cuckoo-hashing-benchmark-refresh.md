# Cuckoo hashing benchmark refresh

## Refresher
- Lookup stays O(1) expected because each key checks at most two candidate positions.
- Insert cost is where the interesting behavior appears: once both slots are occupied, inserts can trigger displacement chains and sometimes a full rehash with new hash salts.
- For a compact benchmark, the clearest story is: as target load factor rises, displacement and rehash counts tend to rise too.

## Quick self-test
- If capacity is 31 and target load factor is 0.6, the benchmark should insert about 19 items.
- If a trial finishes with zero rehashes, its salts should still be deterministic for that trial.
- CSV output should flatten summary metrics, not dump nested per-trial JSON blobs into one cell.
