# Tarjan SCC bottleneck review pass 2

- Scope: CLI/documentation review.
- Checks: ran `condensation` and `explain --limit 4` on `sample_graph.json` and compared output against the README narrative.
- Issue found: the README previously documented topology levels but not the new bottleneck metadata or why it matters.
- Fix applied: expanded the README with incoming/outgoing counts, bottleneck-role definitions, and an updated JSON example.
- Result: the portfolio story now matches the implemented output.
