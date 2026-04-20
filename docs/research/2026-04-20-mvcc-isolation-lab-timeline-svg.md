# MVCC isolation lab timeline/SVG note — 2026-04-20

## Research decision
No extra external web research was needed for this slice.

## Why
- the feature is a presentation/export improvement on top of an already-tested local trace format, not a new database semantics model
- self-contained SVG output can be produced directly from standard XML/SVG primitives already supported by browsers and static portfolio hosting
- the main design work is mapping existing begin/read/write/commit trace events into transaction lanes and committed-version callouts, which is repo-local reasoning rather than vendor-specific behavior

## Design takeaway
- keep the export dependency-free and static-host-friendly
- make commit versions visible in the same artifact so readers can connect the schedule to final state changes quickly
- support both `run --timeline-svg-out` for one isolation mode and `compare --timeline-svg-dir` for batch artifact generation
