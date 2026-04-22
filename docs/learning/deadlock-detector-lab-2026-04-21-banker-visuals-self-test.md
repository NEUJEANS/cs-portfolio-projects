# Deadlock detector Banker visuals self-test

## Quick refresh
- Wait-for and allocation diagrams explain detection after the system is already in or near a stall.
- Banker's algorithm explains avoidance before a new request is granted.
- A good avoidance visual should preserve the real trace data instead of replacing it with generic summary copy.

## Self-test
1. **What must the safety visual show immediately?**
   - whether the state is safe
   - the safe sequence or unfinished set
   - how `work` changes as each process finishes

2. **What must the request visual show immediately?**
   - whether the request is granted or denied
   - the reason for that decision
   - the evaluated available vector and resulting trace

3. **Why embed the Banker visuals inside the dashboard too?**
   - so detection and avoidance both have one-glance diagrams instead of only the detection side feeling visual

## Practical rule for this slice
If a recruiter screenshots the Banker section alone, the decision story should still be understandable without reading the raw JSON first.
