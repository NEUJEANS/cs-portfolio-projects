# extendible-hashing-lab delete/merge self-test — 2026-04-20

## Quick refresh
- Buddy merge is only valid when the target bucket and its buddy have the same local depth.
- After a merge, the surviving bucket drops its local depth by one and both buddy pointer sets must alias the survivor.
- Directory shrink is only safe when no bucket still uses the current global depth and the top/bottom directory halves match.

## Self-test
1. **Q:** Why can't a depth-2 bucket merge with a depth-1 buddy even if they would fit by capacity?
   **A:** Their alias ranges are different sizes, so merging would corrupt the prefix partition represented by the directory.
2. **Q:** What lets the directory shrink from depth 2 to depth 1 after a merge?
   **A:** Every bucket's local depth is now `< 2`, so the two directory halves become redundant views of the same buckets.
3. **Q:** What's the easiest regression to miss after adding delete-time merges?
   **A:** Snapshot round-trips after shrink, because stale directory pointers or surviving bucket depths can still look superficially valid in JSON.
