# 2026-04-15 interval-tree benchmark review pass 2

## What I reviewed
- benchmark argument handling
- failure behavior for obviously invalid workloads

## Issue found
- The benchmark command accepted zero or negative workload values, which could produce misleading or degenerate runs.

## Fix applied
- added explicit validation for `--intervals`, `--queries`, `--start-max`, `--width-max`, and `--query-width-max`
- added a CLI regression test to confirm non-positive interval counts fail with a clear error message
