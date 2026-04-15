# Deadlock Detector Banker's Algorithm Refresh

## Refresher
- `need[i][j] = max[i][j] - allocation[i][j]`
- safety check: repeatedly find an unfinished process whose `need <= work`, mark it finishable, and release its allocation into `work`
- request check: validate `request <= need` and `request <= available`, simulate the grant, then rerun the safety algorithm

## Self-test
1. Why can a request be denied even when resources are currently available?
   - Because granting it may leave the system in an unsafe state with no complete safe sequence.
2. What distinguishes detection from avoidance here?
   - Detection explains whether the current state is deadlocked; avoidance predicts whether a proposed state transition should be allowed.
3. Why store `max` claims explicitly?
   - The algorithm needs declared upper bounds to compute remaining need and reason about future safety.
