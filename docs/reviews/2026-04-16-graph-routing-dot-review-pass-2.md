# Review pass 2 — graph-routing DOT slice

## Focus
Test and documentation review for the new CLI/export surface.

## Issues found
1. The new DOT tests initially asserted rendered-newline behavior incorrectly and also assumed the negative-cycle sample would keep `A` at distance `0`, which is false once the reachable cycle keeps relaxing costs.
2. The README and project checklist needed an explicit DOT export mention so the new slice was discoverable.

## Fixes applied
- corrected the DOT assertions to match literal `.dot` output and to verify negative-cycle styling instead of a bogus fixed distance
- updated the README usage/features/testing notes and the project checklist to document DOT export clearly
