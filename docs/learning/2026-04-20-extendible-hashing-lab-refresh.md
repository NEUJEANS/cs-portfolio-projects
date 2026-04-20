# Extendible hashing refresh + self-test — 2026-04-20

## Quick refresh
- the directory has `2 ** global_depth` slots
- multiple directory slots may alias the same bucket when that bucket's `local_depth` is smaller than `global_depth`
- split rule:
  1. if the target bucket is full and `local_depth == global_depth`, double the directory first
  2. increment the overflowing bucket's `local_depth`
  3. create a sibling bucket with the same new `local_depth`
  4. repoint only the matching directory aliases
  5. redistribute the old bucket's entries using the updated directory
- deletions do not need bucket merge/shrink in the first slice as long as the limitation is documented

## Self-test
- Q: When do you double the directory?
  - A: only when an overflowing bucket already has `local_depth == global_depth`
- Q: Why can two directory entries point to the same bucket?
  - A: because the bucket may only care about fewer hash bits than the full directory currently exposes
- Q: What is the easiest bug to miss in a first implementation?
  - A: repointing the wrong directory aliases during a split, which silently breaks later lookups

## Implementation note
Use a deterministic hash and make the snapshot/inspection output explicit enough that a reviewer can see bucket aliasing without reading the source code.
