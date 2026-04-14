# Cache Simulator Review Pass 1 — 2026-04-14

Findings:
- The trace schema exposed a `size` field but the simulator ignored whether an access crossed a cache block boundary.
- That could mislead readers into thinking multi-byte accesses were modeled correctly.

Fix plan:
- Validate that a single access fits within one cache block for this vertical slice.
- Add a regression test for cross-block access rejection.
