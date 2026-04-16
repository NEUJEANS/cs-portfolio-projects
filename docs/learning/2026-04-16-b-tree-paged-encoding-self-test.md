# B-tree paged encoding self-test

- Timestamp: 2026-04-16 04:57 UTC
- Project: `b-tree-index-lab`

## Refresh prompt
1. What extra metadata is needed beyond a JSON tree snapshot to load a B-tree from fixed-size pages?
2. Why do internal B-tree pages need `len(children) == len(keys) + 1` after decoding?
3. Why is it better to reject values that exceed a fixed page slot than to truncate them?

## Short answers
1. At minimum: format magic/version, tree degree, page size, value-slot size, root page id, page count, and item count.
2. Because each separator key splits the key space into one more child interval than the number of stored separator keys.
3. Silent truncation corrupts logical values and makes round-trip tests lie; explicit failure teaches the storage constraint and keeps the file trustworthy.
