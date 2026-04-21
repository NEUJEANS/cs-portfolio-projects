# library-manager-sqlite borrower policy rules self-test

Date: 2026-04-21

## Quick refresh
- Persisted rules matter more than one-off CLI flags because they keep the project stateful and demoable.
- A single-row policy table is simpler and clearer than a generic settings table when only a few strongly typed rules exist.
- Checkout enforcement and policy reporting should share the same borrower-status logic so the UI story and runtime behavior cannot drift apart.

## Self-test
1. Why persist policy settings in SQLite instead of passing them only as checkout flags?
   - Because the project becomes a real configurable system, and exported reports can show the exact rules that were active when the snapshot was taken.
2. Why avoid SQLite triggers for this slice?
   - Because the CLI needs specific human-readable failure messages and shared logic for both enforcement and reporting. Python-side enforcement is easier to keep transparent.
3. Why export a policy report instead of only printing the config?
   - Because the portfolio value comes from showing borrower compliance, blocked cases, and rule pressure in a recruiter-friendly artifact, not just from storing the settings.
