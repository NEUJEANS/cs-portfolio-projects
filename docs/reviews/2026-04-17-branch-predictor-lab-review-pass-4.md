# branch-predictor-lab review pass 4

## Focus
Predictor-behavior audit for the new `tournament-style` synthetic workload.

## Issue found
The first draft of the new test assumed `gshare` should win with only `--history-bits 1`, but this mixed workload intentionally interleaves a driver branch with other branches. In practice, the correlated follower becomes clearer once gshare has a deeper history window.

## Fix applied
- changed the unit test to compare shallow vs deeper gshare history instead of asserting a one-bit-history win
- added a README command that demonstrates the workload with `--history-bits 4`, which matches the intended teaching story

## Result
The workload still motivates history-aware prediction, but the docs/tests no longer oversimplify how much history it needs.
