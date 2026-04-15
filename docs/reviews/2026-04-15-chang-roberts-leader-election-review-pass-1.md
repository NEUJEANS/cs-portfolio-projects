# Review pass 1 — chang-roberts leader election lab

## Focus
Code correctness and protocol shape.

## Findings
- Core election loop correctly elects the highest active process id.
- Found an unnecessary `active` field on `Node` that was not used anywhere.

## Fixes applied
- Removed the unused `active` field to keep the simulator tighter and easier to explain.
