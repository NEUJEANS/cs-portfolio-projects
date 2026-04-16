# Disk Scheduler LOOK / C-LOOK Refresh

## Goal
Add request-aware elevator variants to the existing disk scheduler lab without changing the JSON-first CLI shape.

## Notes
- **LOOK** behaves like SCAN except the head reverses at the furthest pending request in the current direction instead of sweeping all the way to cylinder `0` or `max_cylinder`.
- **C-LOOK** behaves like C-SCAN except the circular jump goes from the furthest serviced request directly to the first pending request on the other side.
- Relative to SCAN/C-SCAN, the new variants should keep the same service order families while reducing wasted movement when no request exists at the physical edge.
- Direction still matters when one side is empty:
  - LOOK should reverse immediately.
  - C-LOOK should wrap immediately to the furthest request on the other side and continue in the same circular direction.

## Slice target
Implement both algorithms, expose them through `simulate` and `compare`, and lock behavior down with deterministic tests and README examples.
