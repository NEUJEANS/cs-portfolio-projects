# Dependency graph planner research — 2026-04-20 — renewable resource classes

## Brief web research
- Resource-constrained project scheduling (RCPSP) is the standard term for precedence-constrained scheduling with limited shared resources.
- CSPLib problem 061 frames the classical version as DAG precedence constraints plus renewable resources whose capacities cannot be exceeded at any time.
- That maps cleanly onto this project's existing worker-limited list scheduler: keep the deterministic ready queue, but only dispatch a task when both a worker and its optional renewable `resource_class` capacity are available.

## Sources checked
- CSPLib problem 061 — Resource-Constrained Project Scheduling Problem: <https://www.csplib.org/Problems/prob061/>
- Search grounding recap for RCPSP / renewable resource capacity terminology and list scheduling context.

## Practical takeaway for this slice
- Keep the implementation intentionally lightweight and portfolio-readable: one optional `resource_class` per task plus top-level `resource_capacities` is enough to demonstrate real runner-pool constraints without turning the project into a full optimizer.
