# Red-black-tree-lab review pass 1

## Focus
- core invariants and implementation hygiene

## Findings
1. `validate()` checked ordering and colors but not parent-pointer integrity, which makes rotation bugs harder to diagnose.
2. `parse_values()` was unused noise in a compact lab.

## Fixes applied
- added explicit parent-pointer checks to `validate()`
- removed the unused helper
- added a regression test that corrupts a parent pointer and verifies the validator catches it
