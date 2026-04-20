# Two-phase commit lab catalog note — 2026-04-20

## Research decision
No extra external web research was needed for this slice.

## Why
- the protocol semantics were already established in the initial 2PC slice using vendor-backed research on durable prepared state and coordinator recovery
- this follow-up slice is primarily about artifact packaging and comparison clarity, not about introducing a new distributed-transaction rule
- the main design constraints are repo-local: deterministic Markdown output, relative links that work in GitHub browsing, and fast recruiter scanning across multiple scenarios

## Design takeaway
- keep the catalog dependency-free and generated from the same simulation results as the per-scenario reports so there is one source of truth
- make the comparison table answer the protocol story quickly: outcome, decision visibility, crash point, recovery, and how many participants prepared or acknowledged
- include enough per-scenario context directly in the landing page that a reader can understand each case before clicking through to the detailed report
