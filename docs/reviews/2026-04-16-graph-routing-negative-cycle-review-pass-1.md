# graph-routing-negative-cycle-lab review — pass 1 (diff audit)

- Audited the new project layout, README, sample fixtures, test coverage, and root README entry.
- Found one doc-to-output gap: the project claimed Bellman-Ford iteration snapshots for explainability, but pretty-mode output did not mention the iteration log at all.
- Fix applied: added an `Iterations logged:` line to pretty rendering and extended the pretty-output test to lock it in.
