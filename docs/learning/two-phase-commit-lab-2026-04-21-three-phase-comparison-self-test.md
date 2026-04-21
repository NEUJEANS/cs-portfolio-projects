# Two-phase commit lab learning + self-test — 2026-04-21 — 3PC comparison slice

## Quick refresh
- 2PC gives a simple atomic-commit story, but prepared participants can block if the coordinator dies before they learn the durable decision.
- 3PC inserts a commit-ready phase so timeout-driven recovery can avoid indefinite waiting, but only under stronger synchrony assumptions.
- Saga avoids the global prepare barrier entirely, trading strict cross-service atomicity for compensation logic and eventual consistency.

## Self-test
1. **Why add 3PC to this lab if the repo already had 2PC and saga?**  
   Because it fills the conceptual middle ground between strict atomic commit and compensation-first workflows.
2. **What is the honest caveat to repeat every time 3PC is mentioned?**  
   Its non-blocking story depends on bounded delays and no partitions, so it is much more of a teaching protocol than a common production default.
3. **What should this slice avoid?**  
   Pretending the project built a full 3PC simulator when the feature is really a comparison artifact layer on top of the existing scenarios.
