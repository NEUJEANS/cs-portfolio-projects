# MVCC isolation lab refresh + self-test — 2026-04-20

## Quick refresh
- MVCC keeps committed versions around so readers can see a consistent view without blocking every writer.
- `read-committed` usually means each statement sees the latest committed state at statement start, so repeated reads can drift.
- snapshot isolation pins reads to a start-of-transaction snapshot and usually aborts only on write-write conflicts.
- serializable execution has to stop not only direct write-write conflicts, but also schedules whose combined effect could not happen in any serial order.

## Self-test
1. Why can snapshot isolation still allow write skew?
   - Because two transactions can read the same invariant boundary, update different rows, and avoid direct write-write conflict detection.
2. What user-visible behavior should `read-committed` show that snapshot isolation should not?
   - A transaction can read the same row twice and see two different committed values if another transaction commits in between.
3. What compact rule is good enough for this teaching lab's serializable mode?
   - Abort at commit if any key in the transaction's read or write set changed after its start snapshot.

## Implementation guardrails
- keep the scenario DSL tiny: `read`, `assert`, and `write` are enough for a first vertical slice
- prefer deterministic schedules over threads so the artifact is easy to reproduce in tests and screenshots
- make final invariants explicit so the portfolio story says more than “the code ran”
