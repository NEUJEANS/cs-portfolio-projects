# Deadlock detector Banker trace self-test

## Quick refresh
- A Banker's safety pass uses `work`, `allocation`, `max`, and `need = max - allocation`.
- A process is runnable when every remaining-need component is less than or equal to the current `work` vector.
- After a runnable process finishes, its allocation is released back into `work`.

## Self-test
1. **What has to be true before tentatively granting a request?**
   - The request must not exceed the process's remaining need.
   - The request must not exceed currently available resources.
   - The simulated post-grant state must still be safe.

2. **What should a useful trace step show?**
   - `work` before the choice
   - which processes were runnable at that moment
   - the chosen process
   - the allocation released
   - `work` after the release

3. **What should an unsafe export add beyond `safe: false`?**
   - which unfinished processes remain blocked
   - the exact resource shortages at the stall point

## Practical rule for this slice
Prefer trace data that explains *why* the next step is valid, not just the final safe sequence.
