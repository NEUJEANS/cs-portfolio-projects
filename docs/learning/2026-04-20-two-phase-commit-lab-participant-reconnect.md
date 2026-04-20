# Two-phase commit lab participant reconnect refresh + self-test — 2026-04-20

## Quick refresh
- in plain 2PC, a participant that has written a durable PREPARED record cannot decide on its own; if it misses the final decision message, it stays uncertain until recovery or a retry answers the question
- the simulator should keep the global outcome tied to the durable coordinator decision, while the participant row/report can show whether the decision was learned immediately or after reconnect
- deterministic artifacts matter more than protocol theater: the new scenario should regenerate the same Markdown every run and plug cleanly into the existing catalog

## Self-test
1. Why keep the scenario outcome as `commit` in a reconnect-recovery case instead of inventing a new global outcome?
   - because the global decision was already durably recorded; the reconnect only changes when one participant learns it, not what the decision is.
2. Why model missed delivery on the participant rather than only through coordinator crash points?
   - because participant uncertainty can happen even when the coordinator stays healthy; it is a different operational story from coordinator crash recovery.
3. What needs to show up in the report so the slice is visible to recruiters?
   - the participant table should show the second-phase delivery mode and whether recovery happened after reconnect, and the catalog should summarize reconnect recoveries too.

## Guardrails
- do not break the simple happy-path/abort/blocking cases while adding reconnect handling
- keep the CLI surface small; extend the existing scenario schema instead of inventing a brand-new command
- prefer one strong committed reconnect scenario over multiple half-finished variations
