# mvcc-isolation-lab Checklist

- [x] do brief research on MVCC isolation levels, snapshot write skew, and serializable validation semantics
- [x] refresh the concurrency-control model with a short self-test note before coding
- [x] add a new database-isolation portfolio lab instead of another data-structure variant
- [x] implement scenario validation plus step-by-step simulation for `read-committed`, `snapshot`, and optimistic `serializable`
- [x] add sample scenarios for write skew and repeatable-read behavior
- [x] add Markdown comparison export and committed example artifacts under `docs/artifacts/mvcc-isolation-lab/`
- [x] add automated tests for validation, simulation semantics, and CLI export output
- [x] complete at least 3 review passes and fix issues found
- [x] run tests, secret scan, commit, push, and wrap up the slice
- [x] add timeline/SVG artifacts for transaction windows and version changes
- [x] add predicate/range-query phantom examples
- [x] add lock-based serialization mode for contrast with optimistic validation
- [x] add a static HTML dashboard export that summarizes scenario footprint, abort causes, and links to Markdown/SVG artifacts
