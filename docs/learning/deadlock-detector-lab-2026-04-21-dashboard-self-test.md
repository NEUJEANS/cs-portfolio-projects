# Deadlock detector dashboard self-test

## Quick refresh
- Wait-for detection is a process-only cycle check, so it is strongest for single-instance blocking stories.
- Allocation-progress detection can still find progress even when some edges look blocked, because finished processes release held resources back into `work`.
- Banker's algorithm is about avoiding unsafe grants before the system enters deadlock.

## Self-test
1. **What question does each panel answer?**
   - Wait-for graph: is there already a process cycle?
   - Allocation snapshot: can the current `work` vector finish anyone and break the stall?
   - Banker's safety/request: is the state safe, and should a new request be granted?

2. **Why include both safety and request traces in the same dashboard?**
   - The safety trace shows the baseline safe completion story.
   - The request trace shows how avoidance makes a go or no-go decision on a concrete request.

3. **What should the combined artifact avoid?**
   - Repeating the same summary text in every panel.
   - Hiding the input sources or decision reason.
   - Depending on JS or external assets just to open the report.

## Practical rule for this slice
Make the comparison panel answer "detection versus avoidance" faster than reading four separate artifacts would.
