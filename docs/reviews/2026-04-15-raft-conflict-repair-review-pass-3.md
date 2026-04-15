# Review pass 3 — docs and usability audit

## Focus
Ensure the README and checklist reflect the new behavior so the project remains resumable.

## Findings
1. README wording still described replication as generic heartbeats/commits.
2. The unfinished checklist item for `prevLogIndex` / `prevLogTerm` repair had not been marked complete.
3. The new demo hook needed to be documented explicitly.

## Fixes applied
- Updated README features/design notes to mention `nextIndex` / `matchIndex`, append rejection, and conflict repair.
- Documented the `force-log` scenario step.
- Marked the conflict-repair checklist item complete and left the next future slice clearly queued.

## Result
The project docs now match the implemented behavior and make the next iteration obvious.
