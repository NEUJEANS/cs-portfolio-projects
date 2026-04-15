# Count-Min Sketch + Top-K Heavy Hitters Research

Date: 2026-04-15

## Goal
Add a stronger streaming heavy-hitter story to the Count-Min Sketch lab without turning it into a large framework.

## Brief findings
- Count-Min Sketch is excellent for compact, mergeable approximate frequency estimates, but by itself it does not maintain a bounded candidate set for top-k heavy hitters.
- A standard practical pairing is CMS + a bounded heavy-hitter summary such as Space-Saving.
- Space-Saving keeps a fixed number of monitored items. When full, a new unseen item replaces the minimum-count entry, inheriting its count plus the new increment and storing the dropped count as an error bound.
- This gives a very portfolio-friendly narrative: CMS provides broad approximate counts, while the bounded summary keeps a live candidate set for top-k reporting.

## Implementation choice for this slice
- Add an in-process Space-Saving style summary to the lab.
- Keep it optional via a `top_k_capacity` configuration so the core CMS behavior stays intact.
- Persist the summary in JSON save/load so runs remain resumable.
- Expose a CLI command to report the tracked top-k candidates.

## References checked
- Wikipedia summary of Count-Min Sketch concepts and one-sided error behavior.
- Search-grounded overview noting common CMS + Space-Saving pairing for top-k / heavy hitter tracking.

## Constraints
- Keep the code small and readable for students.
- Preserve deterministic output for tests.
- Avoid adding extra dependencies.
