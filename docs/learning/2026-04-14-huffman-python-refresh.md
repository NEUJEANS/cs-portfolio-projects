# 2026-04-14 Python Refresh for Huffman Compressor

Short refresh before implementation:
- `heapq` is the simplest standard-library fit for the Huffman priority queue.
- `collections.Counter` keeps byte-frequency counting concise and readable.
- `pathlib.Path` is enough for binary-safe file IO in a CLI project.
- A dataclass with `order=True` lets heap nodes compare by frequency without custom comparator code.

## Mini self-check
1. Can I build a min-heap from `(frequency, symbol)` pairs? Yes.
2. Can I serialize a compact header without extra dependencies? Yes, JSON header + raw encoded bytes is enough for this slice.
3. How should a one-symbol input behave? Assign code `0` so compression/decompression still round-trips.
