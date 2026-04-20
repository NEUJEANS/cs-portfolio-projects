# Dependency Graph Planner Research - 2026-04-19

## Goal
Add a portfolio-friendly slice that moves beyond unlimited parallel layers and shows what happens when the same DAG must run with a fixed worker cap.

## Brief scheduling points reviewed
- precedence-constrained list scheduling is a natural next step after topological planning because tasks can only start once dependencies finish and a worker is free
- a realistic lower bound for any worker-limited schedule is `max(critical_path_length, ceil(total_work / workers))`
- deterministic tie-breaking matters for portfolio artifacts just as much here as it does for topological order; the same manifest should produce the same worker timeline every run
- surfacing queue delay helps explain *why* a worker cap slowed the run, not just *that* the makespan increased

## Notes carried into implementation
- keep the worker-limited scheduler dependency-free and event-driven so the code stays interview-friendly
- reuse existing slack / critical-path data to prioritize ready work deterministically
- expose both machine-readable JSON and recruiter-friendly Markdown so the feature is useful for scripts and portfolio screenshots
- keep the first slice focused on fixed identical workers; richer heuristics and resource classes can come later
