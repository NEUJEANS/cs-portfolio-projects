# Two-phase commit lab protocol-comparison research note — 2026-04-20

## Sources checked
- PostgreSQL 18 docs — Two-Phase Transactions: https://www.postgresql.org/docs/current/two-phase.html
- microservices.io — Saga pattern: https://microservices.io/patterns/data/saga.html

## Brief findings
- PostgreSQL's `PREPARE TRANSACTION` / `COMMIT PREPARED` / `ROLLBACK PREPARED` flow is a concrete reminder that 2PC revolves around a durable prepared state and a later authoritative global decision.
- The PostgreSQL docs also call out that prepared transactions are intended to be short-lived, which reinforces the portfolio lesson that long waits in PREPARED state are operationally painful.
- The saga pattern is the right contrast for this lab because it replaces one global atomic commit barrier with a sequence of local transactions plus compensations.
- For this repo's audience, the strongest comparison is not abstract CAP-theory language; it is the incident-response difference between (a) blocked prepared peers waiting on a coordinator-owned durable decision and (b) resumable or compensatable workflow state that avoids PREPARED lock blocking.

## Design takeaway
- keep the simulator's baseline grounded in plain 2PC semantics instead of pretending saga is a drop-in replacement with the same guarantees
- make the comparison artifact scenario-specific so the reader can ask, "what would this exact failure look like under saga instead?"
- explicitly surface peer-visible durable-decision hints in blocked-after-decision cases, because those scenarios are subtler than the classic pure blind-wait crash
