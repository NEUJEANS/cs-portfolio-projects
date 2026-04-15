# Chord stabilization export review pass 2

- Reviewed the Markdown rendering with an unfinished four-round join scenario.
- Issue found: unfinished modes rendered `None` in the "Stabilized round" column, which reads like raw Python instead of portfolio-facing prose.
- Fix applied: render `not within budget` when the run does not fully stabilize within the requested rounds.
