# B-tree paged encoding notes

- Timestamp: 2026-04-16 04:55 UTC
- Project: `b-tree-index-lab`
- Goal: turn the earlier JSON snapshot serializer into a more storage-realistic fixed-size page format.

## Quick refresh
- Database/file-system B-trees are usually stored as fixed-size pages so a node can be read or written with one page-sized I/O.
- A practical teaching version can reserve fixed slots for keys, values, and child pointers even if that wastes some padding, because the layout becomes inspectable and deterministic.
- For a compact student portfolio artifact, a binary header + contiguous page table is enough to demonstrate page-level thinking without dragging in a full slotted-page implementation.

## Slice direction
- Add a binary `save-pages` format with:
  - file magic/version metadata
  - tree-wide degree, page size, value slot size, root page id, and item count
  - one fixed-size page per B-tree node
- Keep values UTF-8 encoded with a 2-byte length prefix inside each fixed slot.
- Reject oversized values or undersized page layouts early so the CLI teaches capacity constraints instead of silently truncating data.

## Tradeoff note
- This is intentionally simpler than a production slotted-page layout.
- Fixed value slots are less space-efficient, but they make the encoded pages easy to reason about in interviews and easy to round-trip in tests.
