# Two-phase commit lab learning — 2026-04-20 — HTML comparison dashboard

## Quick refresh
- Reused the existing comparison payload instead of inventing a dashboard-only schema.
- Kept the artifact static and deterministic: no timestamps, no random IDs, no client-side JavaScript.
- Surfaced the most interview-relevant facts first: baseline 2PC outcome, saga contrast, informed peers, termination hint, and crash point.

## Self-test
- Q: What is the one fact a recruiter should notice first in the classic blocked case?
  - A: 2PC blocks because PREPARED participants cannot prove a durable decision, while saga pauses without holding a global PREPARE barrier.
- Q: What is the one fact they should notice first in the partial-delivery blocked case?
  - A: The incident is still blocked, but `inventory` already knows `COMMIT`, so the story becomes peer-assisted termination rather than blind waiting.
- Q: Why keep the dashboard static instead of adding JavaScript filters?
  - A: The repo benefits more from deterministic committed artifacts than from interactive complexity for this slice.
