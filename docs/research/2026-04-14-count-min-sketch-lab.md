# Count-Min Sketch Lab Research Notes

## Why this project
- Adds another strong streaming/probabilistic-data-structure project after HyperLogLog and Bloom filter work.
- Gives a clean interview story around approximate counting, mergeable summaries, and heavy-hitter detection.
- Stays small enough for a single vertical slice while leaving obvious room for benchmark and top-k follow-ups.

## Concept reminders
- Error is one-sided: collisions can overestimate counts, but the minimum-of-rows query avoids underestimation.
- `epsilon` controls additive error relative to total stream size; `delta` controls failure probability.
- Sketches are mergeable only when they share the same dimensions and hash family/seed.

## Slice chosen for this run
Implement a polished baseline lab with:
- core sketch operations
- CLI for build / estimate / heavy-hitters / merge
- JSON serialization for resumable workflows
- tests and review notes
