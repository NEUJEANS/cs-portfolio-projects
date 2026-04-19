# Learning refresh — dirty-page-aware WSClock

## Refreshed concepts
- Dirty bit: page was modified in memory and needs writeback before safe reuse.
- WSClock preference order in this simulator:
  1. empty slot
  2. referenced page gets another chance
  3. old clean page can be evicted now
  4. old dirty page gets a writeback scheduled and may become reclaimable on a later pass
  5. fallback remains least-recently-used-ish among scanned pages
- `tau` still matters even after adding dirty pages: a tighter window can expose more cleaning pressure because pages age out sooner.

## CLI refresh
- `--dirty-page <n>` repeats to mark write-heavy pages.
- `--dirty-pages-file <path>` loads a reusable list for repeatable demos.
- compare/study/gallery/aggregate/trace-compare now all surface dirty-page metadata and WSClock writeback counts.

## Portfolio angle
This slice makes the project more realistic for OS interviews because it no longer treats every eviction as equally cheap. It now shows the difference between:
- fewer faults
- lower writeback pressure
- and how those goals can diverge.
