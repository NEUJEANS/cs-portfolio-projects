# Quadtree Spatial Index Lab Review - Pass 2

## Focus
Portfolio quality and observability.

## Issues found
1. The project exposed queries but gave no quick way to show how much subdivision happened.
2. There was no direct test coverage for tree shape statistics after subdivision.

## Fixes applied
- added `point_count`, `node_count`, and `max_observed_depth` helpers
- added a `stats` CLI command that prints compact JSON tree metrics
- added unit and CLI tests for the new stats output
