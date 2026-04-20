# Two-phase commit lab protocol comparison refresh + self-test — 2026-04-20

## Quick refresh
- 2PC gives strong all-or-nothing atomicity because every participant waits for one coordinator-owned durable decision before finalizing.
- Saga is a useful contrast for service-oriented systems because it breaks the work into local commits plus compensations instead of holding PREPARED participants behind one global barrier.
- A blocked 2PC scenario is not always identical: some crashes leave every prepared peer uncertain, while others leave at least one peer already knowing the durable decision and therefore able to help through termination-protocol checks.

## Self-test
1. Why compare 2PC with saga instead of saying saga is just a better 2PC?
   - because the guarantees differ: 2PC aims for one global atomic outcome, while saga accepts weaker isolation and uses compensation instead of a single shared commit point.
2. What should the artifact show for a crash-after-decision-log case with one peer already informed?
   - that the 2PC run is still blocked for some participants, but it is a peer-assisted recovery story rather than pure blind waiting because an informed participant can relay the durable decision.
3. What makes the comparison portfolio-worthy instead of just theoretical notes?
   - a recruiter can run the same scenario through the CLI, read committed Markdown/JSON artifacts, and see the trade-off tied to a concrete incident rather than hand-wavy architecture claims.

## Guardrails
- keep the saga language precise: eventual consistency and compensation, not fake global rollback
- preserve deterministic artifacts so repeated exports stay commit-friendly
- make the comparison output explain the incident clearly without requiring the reader to inspect source code first
