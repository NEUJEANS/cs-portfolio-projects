# Python Refresh + Self-Test for Vector Clock Lab

## Refresh topics
- dataclasses for small immutable value objects
- dictionary normalization for sparse replica counters
- argparse subcommands for a small simulation CLI
- pytest assertions for ordering and conflict behavior

## Self-test
1. If clock A has every component <= clock B and at least one component is smaller, then A happened before B.
2. If neither clock dominates the other, the events are concurrent.
3. Merging two clocks is a component-wise max.
4. A resolved version should increment the resolving replica after merging ancestor clocks so the result is causally newer.

## Result
Passed the refresh checklist and used it to drive the implementation and tests.
