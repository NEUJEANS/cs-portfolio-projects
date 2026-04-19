# Graph routing negative-cycle lab HTML dashboard review — 2026-04-19

## Pass 1 — determinism audit
- Reviewed the new static HTML export with the goal of committing a stable artifact under `docs/artifacts/`.
- Issue found: the dashboard stamped a live UTC generation timestamp into the HTML, so rerunning the same command rewrote the committed artifact even when the comparison data was unchanged.
- Fix applied: removed the live timestamp dependency and replaced it with deterministic meta copy (`Deterministic static artifact`).
- Validation: reran the HTML export twice and confirmed the committed output stayed stable aside from the intentional first creation.

## Pass 2 — terminology correctness audit
- Reviewed the card/table labels against the actual Bellman-Ford data model used by the lab.
- Issue found: the dashboard called the stored `predecessor` field a "next hop", which is inaccurate because the value is the predecessor/parent in the shortest-path tree, not the source router's first hop.
- Fix applied: renamed the HTML-facing labels and summary card copy to `predecessor` / `Predecessor changes` / `Predecessor shift`.
- Validation: extended the HTML regression test expectations and regenerated the sample dashboard artifact.

## Pass 3 — same-cost reroute readability audit
- Reviewed the route cards for the sample graph where node `D` reroutes but keeps the same total path cost.
- Issue found: the dashboard displayed a `+0` delta, which looked like a noisy numeric change instead of reinforcing that the route changed at the same cost.
- Fix applied: formatted zero cost deltas as `unchanged` in the HTML metrics.
- Validation: reran `python3 -m py_compile projects/graph-routing-negative-cycle-lab/graph_routing_lab.py`, `python3 -m unittest tests.test_graph_routing_negative_cycle_lab`, regenerated the HTML artifact, and reran `git diff --check`.
