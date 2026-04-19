# Learning refresh — WSClock tuning

## Refreshed concepts
- `tau` is a policy knob, not a universal constant. The same workload can keep page faults flat while sharply changing writeback pressure.
- A weighted score like `faults + penalty × writebacks` is a simple way to teach multi-objective tuning without pretending the simulator models every storage detail.
- The Pareto frontier matters because two windows can both be reasonable depending on whether the operator cares more about memory misses or background disk pressure.

## CLI refresh
- `tune-wsclock` now sweeps a candidate range instead of forcing manual one-off comparisons.
- `--writeback-penalty` makes the recommendation criteria explicit instead of hiding it inside the implementation.
- Markdown / CSV / JSON exports make the sweep reproducible and easy to cite in portfolio material.

## Portfolio angle
This slice upgrades the project from a simulator into a small analysis tool. A student can now show:
- how the same algorithm behaves under multiple `tau` settings
- why a fixed recommendation was chosen for a concrete workload and frame budget
- and how dirty-page pressure can change the best answer even when page-fault counts are similar
