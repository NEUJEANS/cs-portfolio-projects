# Distance vector routing count-to-infinity research — 2026-04-15

## Goal
Strengthen the routing lab by showing the classic failure mode people actually discuss in interviews: routes that keep increasing after a failure when routers trust stale neighbor information.

## Brief findings
- Count-to-infinity is easiest to demonstrate when the post-failure simulation starts from already-converged tables instead of recomputing from scratch on the broken topology.
- A tiny line topology (`A-B-C`) with link `B-C` removed is enough to show the problem: `A` and `B` keep re-advertising stale reachability to `C` under classic mode.
- Split horizon and poison reverse are strongest when shown against that same scenario, because the contrast is immediate in the per-round history.
- A compact round-by-round timeline artifact is more portfolio-friendly than dumping the full nested JSON history into a README.

## Slice choice
Implement failure reconvergence from converged pre-failure state, then add Markdown/Mermaid timeline export for one destination across selected routers.
