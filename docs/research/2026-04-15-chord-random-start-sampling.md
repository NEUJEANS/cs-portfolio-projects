# Chord random start-node sampling notes — 2026-04-15

## Goal
Improve the synthetic benchmark so larger Chord rings can be sampled from varied starting positions without always benchmarking the first N sorted nodes.

## Notes
- Using only the first sorted nodes can bias the benchmark toward a narrow region of the ring, especially when start-node count is much smaller than total node count.
- The slice should remain portfolio-friendly and reproducible, so random selection needs an explicit seed and visible metadata in the output payload.
- Backward compatibility matters because earlier docs and tests already rely on ordered start-node selection.

## Implementation direction
- keep the existing `first` behavior as the default mode
- add a helper that validates the requested subset size and supports `first` or seeded `random` selection
- surface `start_node_sample_mode` and `start_node_seed` in the generator metadata
- extend tests to cover helper determinism, error handling, and CLI integration
