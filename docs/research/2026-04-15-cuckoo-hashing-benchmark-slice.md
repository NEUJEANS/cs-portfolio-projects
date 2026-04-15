# Cuckoo hashing benchmark slice research

## Goal
Add a benchmark mode to the existing cuckoo hashing lab so the project can demonstrate how displacement chains and rehash pressure evolve as the table gets denser.

## Notes
- Cuckoo hashing discussions usually focus on constant-time lookup, but portfolio reviewers also want to see how insertion costs shift as load factor rises.
- The most interview-useful metrics for a compact CLI benchmark are load factor, displacement count, rehash count, and elapsed insertion time.
- A deterministic benchmark should vary salts per trial but keep key generation reproducible so results are comparable across runs.
- CSV export is useful because students can quickly chart the benchmark in spreadsheets or notebooks without adding plotting dependencies.

## Planned slice
- add a benchmark helper that inserts synthetic key/value pairs up to target load factors
- report aggregate metrics plus per-trial rows in JSON output
- support optional CSV export for plotting and discussion
- extend README and tests so the benchmark flow is documented and regression-safe
