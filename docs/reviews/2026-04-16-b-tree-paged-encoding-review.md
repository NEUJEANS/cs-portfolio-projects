# B-tree paged encoding review log

- Timestamp: 2026-04-16 05:05 UTC
- Project: `b-tree-index-lab`

## Review pass 1 — serializer traversal
- Issue found: `save_paged()` used `list.pop(0)` for breadth-first traversal, which adds avoidable O(n) queue churn as node counts grow.
- Fix: switched traversal to `collections.deque` + `popleft()`.

## Review pass 2 — decode robustness
- Issue found: `load_paged()` assumed page ids matched read order, which could mis-wire child pointers if page metadata was reordered or validated out of order.
- Fix: build nodes in a `page_id -> node` map, resolve child links through that map, and raise a clear error if a child page is missing.

## Review pass 3 — CLI/storage smoke check
- Check run: save a paged file from `sample_records.json`, reload it via `--page-file`, and compare item/stats output.
- Result: round-trip behavior was correct after the fixes above; no further code change needed.
