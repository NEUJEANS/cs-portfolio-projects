# Two-phase commit lab refresh + self-test — 2026-04-20

## Quick refresh
- phase one asks every participant to `PREPARE`; a YES vote means the participant has durable enough local state to either commit later or roll back under coordinator direction
- phase two is only safe after the coordinator records a durable global decision (`COMMIT` or `ABORT`)
- the classic weakness of plain 2PC is blocking: prepared participants can be stuck waiting if the coordinator crashes before the final outcome is known

## Self-test
1. Why is a YES vote stronger than "I want to commit"?
   - because the participant must be able to honor the later global decision durably, not just express preference.
2. What changes when the coordinator crashes after logging COMMIT versus before logging any decision?
   - after logging COMMIT, recovery can replay the durable outcome; before logging any decision, recovery cannot prove COMMIT and the safe fallback is ABORT.
3. Why keep the first slice deterministic instead of modeling retries, network jitter, and arbitrary message reordering?
   - because the initial portfolio value is explaining the protocol clearly; richer fault modeling can come in later slices once the baseline semantics are easy to inspect.

## Guardrails
- keep scenario JSON compact enough that each case can be read in under a minute
- treat durable decision logging as a first-class event in traces and reports
- preserve resumability by leaving room for later catalog/dashboard and 3PC comparison slices
