# Distance vector routing count-to-infinity review log

## Review pass 1
Issue found: the original `simulate-failure` path rebuilt routing tables from the failed topology, which erased the stale-route state needed for a real count-to-infinity demo.
Fix: added a dedicated failure simulation path that starts the post-failure rounds from the converged pre-failure tables.

## Review pass 2
Issue found: raw nested JSON history is correct but awkward for README screenshots or quick explanation.
Fix: added focused timeline export for one destination across selected routers in Markdown and Mermaid formats.

## Review pass 3
Issue found: my first timeline expectation assumed the infinity metric would be reached within 8 rounds, which was too optimistic for the classic synchronous update sequence.
Fix: extended the regression coverage to longer classic-mode failure runs and documented the timeline workflow with a realistic `--max-rounds 20` example.
