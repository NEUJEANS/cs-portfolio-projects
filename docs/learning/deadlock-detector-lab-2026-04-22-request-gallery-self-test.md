# Deadlock detector Banker request gallery self-test

## Quick refresh
- A request is grantable only if it stays within declared need, fits current availability, and leaves a safe sequence after the simulated allocation.
- The strongest granted-vs-denied comparison is whether the trial still leaves any runnable process.
- Side-by-side outputs should make the contrast visible without opening raw JSON.

## Self-test
1. **What should the granted card show immediately?**
   - granted decision
   - first runnable set after the trial
   - safe sequence and evaluated available vector

2. **What should the denied card show immediately?**
   - denied decision
   - no runnable process after the trial
   - blocking shortages that explain the unsafe state

3. **Why add a gallery command instead of only another sample file?**
   - because recruiters and reviewers can compare both request paths in one artifact instead of mentally diffing separate pages
