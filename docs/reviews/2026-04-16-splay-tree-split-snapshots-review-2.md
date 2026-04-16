# Review Pass 2 — 2026-04-16 — splay-tree-lab split snapshot persistence

## Focus
- edge cases for empty partitions and resumable snapshot metadata

## What I checked
- reviewed `SplitResult` defaults and persisted snapshot serialization
- checked present-pivot behavior where one partition can be empty

## Issue found
- there was no explicit test proving empty partitions preserve `null` root metadata cleanly

## Fix applied
- added `test_split_tracks_empty_partition_roots` to cover a present pivot that leaves the left side empty while keeping the right side resumable
