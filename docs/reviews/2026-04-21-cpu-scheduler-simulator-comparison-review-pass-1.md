# CPU Scheduler Simulator Review — 2026-04-21 Comparison Pass 1

## Focus
Compare report readability and whether the Markdown dashboard exposed the same metrics it highlighted.

## Findings
1. The Markdown takeaways called out throughput winners, but the comparison table itself did not include a throughput column, which made the conclusion harder to verify at a glance.

## Fixes made
- added a dedicated throughput column to the Markdown comparison table
- mirrored the same throughput column in the HTML dashboard table so both artifact formats stay aligned
