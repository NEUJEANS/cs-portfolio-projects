# 2026-04-15 interval-tree benchmark review pass 1

## What I reviewed
- benchmark CLI payload shape
- whether the new benchmark output stayed portfolio-friendly and inspectable

## Issue found
- The first benchmark implementation inherited the full tree summary, including the entire inorder traversal, which made benchmark output noisy and obscured the performance metrics.

## Fix applied
- trimmed benchmark output to compact tree metadata (`tree_height`, `root`, `max_end`, validation state) plus workload/metric fields
- kept full inorder output for the existing structural commands where it is still useful
