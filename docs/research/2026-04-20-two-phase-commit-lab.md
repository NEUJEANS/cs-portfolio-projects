# Two-phase commit lab research note — 2026-04-20

## Sources checked
- PostgreSQL two-phase transaction docs: https://www.postgresql.org/docs/current/two-phase.html

## Brief findings
- PostgreSQL's `PREPARE TRANSACTION`, `COMMIT PREPARED`, and `ROLLBACK PREPARED` flow is a concrete real-world reminder that 2PC depends on a durable prepared state before the final decision is delivered.
- The key operational lesson for this portfolio lab is not vendor-specific syntax; it is the protocol fact that prepared work can outlive the coordinator briefly, and that a durable decision log is what lets recovery finish safely.
- That makes two teaching cases worth emphasizing in code: (1) crash before the durable decision, which blocks prepared participants until recovery, and (2) crash after the durable decision, where replay can safely complete phase two.

## Design takeaway
- keep the simulator coordinator-centric and deterministic for the first slice so the commit/abort/blocking story is obvious
- model durable decision logging explicitly instead of hiding it behind generic state names
- ship committed scenarios that cover both the happy path and the failure modes recruiters are more likely to ask about
