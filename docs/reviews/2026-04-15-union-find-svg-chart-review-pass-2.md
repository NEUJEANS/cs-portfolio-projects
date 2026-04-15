# Review pass 2 — union-find SVG chart slice

- audited CLI argument interactions and failure paths
- issue found: chart-specific flags could be passed without an actual chart-producing mode, which would be confusing in cron runs
- fix applied: added explicit validation for `--output-chart` and `--chart-title` requirements and covered those negative paths in tests
