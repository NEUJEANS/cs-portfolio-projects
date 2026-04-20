# MVCC Isolation Lab

A compact Python simulator that compares `read-committed`, `snapshot`, optimistic `serializable` validation, and a teaching-oriented `strict-2pl` locking model on hand-authored transaction schedules so students can show concurrency-control intuition with runnable code instead of only theory notes.

## Why this project is portfolio-worthy
- demonstrates database-concurrency fundamentals that show up in MVCC engines, optimistic concurrency control, and interview system-design discussions
- turns isolation-level theory into a reproducible CLI with traceable schedules, commit/abort decisions, and invariant checks
- gives you concrete examples for write skew, repeatable-read behavior, and why serializable validation is stricter than snapshot isolation
- stays dependency-free and small enough to study in one sitting while still being extensible for richer anomaly demos later

## Features
- JSON scenario loader with validation for records, transactions, schedules, and invariants
- step-by-step simulation for `read-committed`, `snapshot`, optimistic `serializable`, and teaching-oriented `strict-2pl` locking
- buffered writes plus per-transaction snapshots so traces explain what each transaction could actually see
- safe expression evaluator for scenario `assert` and `write` steps using booleans, arithmetic, comparisons, and a tiny `count_prefix(...)` helper for invariant checks
- lock-conflict traces for `strict-2pl`, including point-key shared/exclusive lock conflicts and predicate-lock conflicts for scan-driven phantom protection
- predicate/range-style `scan` steps that count matching rows by key prefix so the lab can model phantom anomalies alongside simple point reads
- invariant checks that make schedule-level correctness visible in the final output
- comparison mode that replays the same scenario across all supported isolation levels
- Markdown comparison export for recruiter-friendly artifact snapshots in `docs/artifacts/`
- static HTML comparison dashboard export that links the Markdown summary and per-isolation timelines in one browseable page
- multi-scenario gallery/catalog export that regenerates every committed scenario dashboard plus a single landing page for the full lab
- self-contained SVG schedule exports that show begin/read/write/commit ordering plus committed version changes without needing a browser app or external assets
- committed sample scenarios for write skew, repeatable-read drift, and predicate/range-query phantom behavior

## Project structure
- `mvcc_isolation_lab.py` - scenario validation, simulator, Markdown/HTML/SVG artifact rendering, and CLI entrypoint
- `doctor_on_call.json` - classic write-skew scenario where two doctors each sign off based on the same stale snapshot
- `repeatable_read_window.json` - compact scenario that shows a long-running reader under a concurrent writer
- `conference_room_booking_phantom.json` - booking-slot scan scenario where predicate conflicts matter more than key-based overlap
- `CHECKLIST.md` - resumable project checklist for future slices
- `tests/test_mvcc_isolation_lab.py` - regression tests for validation, isolation semantics, and CLI exports
- `docs/artifacts/mvcc-isolation-lab/` - committed Markdown/HTML comparison artifacts, gallery landing pages, and SVG schedule timelines generated from the sample scenarios

## Scenario format
```json
{
  "records": {"inventory": 5},
  "transactions": [
    {
      "name": "Reader",
      "steps": [
        {"op": "read", "key": "inventory", "as": "first_seen"},
        {"op": "assert", "expr": "first_seen >= 0"}
      ]
    }
  ],
  "schedule": ["Reader"],
  "invariants": [
    {"name": "inventory_non_negative", "expr": "inventory >= 0"}
  ]
}
```

### Supported step types
- `read` - reads a key from the transaction's visible view and stores it under `as` (defaults to the key name)
- `scan` - counts keys visible under a `key_prefix` (optionally filtered by `value_equals`) and stores the count under `as`
- `assert` - evaluates an expression against the visible state plus prior local aliases; aborts the transaction when false
- `write` - buffers a literal `value` or computed `expr` until commit time

Expressions used by `assert`, `write`, and final invariants can also call `count_prefix(prefix, value?)` to count visible matching rows in the current state snapshot.

### Isolation model used in the lab
- `read-committed` - each read sees the latest committed state at that step, plus the transaction's own buffered writes
- `snapshot` - each transaction reads from the committed snapshot captured when it began; commit aborts only on write-write conflicts that happened after the snapshot
- `serializable` - uses the same read snapshot as `snapshot`, but commit validation aborts when any key in the transaction's read or write set changed since its snapshot, or when a previously scanned predicate/range result changed before commit
- `strict-2pl` - acquires shared locks for reads, exclusive locks for writes, and shared predicate locks for scans; instead of modeling wait queues and deadlock detection, the teaching model aborts immediately on lock contention so the conflict stays explicit in the trace

This `serializable` mode is intentionally a small optimistic validation model for teaching, not a vendor-exact implementation of PostgreSQL SSI or every serializable database. The `strict-2pl` mode is also intentionally simplified: it shows lock-based serializability and phantom protection, but chooses deterministic abort-on-conflict behavior instead of simulating a full lock manager with waiting and deadlock resolution.

## Usage
Run from the repository root.

### Validate a scenario
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py validate \
  projects/mvcc-isolation-lab/doctor_on_call.json
```

### Run one isolation level
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py run \
  projects/mvcc-isolation-lab/doctor_on_call.json \
  --isolation snapshot
```

### Emit the full JSON result for scripting
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py run \
  projects/mvcc-isolation-lab/repeatable_read_window.json \
  --isolation read-committed \
  --json
```

### Compare all isolation levels at once
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare \
  projects/mvcc-isolation-lab/doctor_on_call.json
```

### Export a Markdown comparison artifact
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare \
  projects/mvcc-isolation-lab/doctor_on_call.json \
  --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md
```

### Export one schedule as a self-contained SVG timeline
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py run \
  projects/mvcc-isolation-lab/doctor_on_call.json \
  --isolation serializable \
  --timeline-svg-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_serializable_timeline.svg
```

### Export a browsable HTML dashboard with companion Markdown and timelines
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare \
  projects/mvcc-isolation-lab/doctor_on_call.json \
  --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md \
  --timeline-svg-dir docs/artifacts/mvcc-isolation-lab \
  --html-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_dashboard.html
```

### Export all isolation timelines for the same scenario
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare \
  projects/mvcc-isolation-lab/repeatable_read_window.json \
  --timeline-svg-dir docs/artifacts/mvcc-isolation-lab
```

### Rebuild the full scenario gallery and landing page
```bash
python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py catalog \
  projects/mvcc-isolation-lab \
  --output-dir docs/artifacts/mvcc-isolation-lab
```

## What the committed samples show
- `doctor_on_call.json`
  - `snapshot` lets both doctors commit because they update different rows, which violates the final coverage invariant
  - `serializable` aborts one doctor because its read set overlaps with a key changed after its snapshot
  - `strict-2pl` also preserves the invariant, but it does so earlier by aborting a writer on a lock-upgrade conflict caused by the other doctor's shared read lock
  - the committed SVG exports make the overlap visible by showing both transactions starting from version `v0`, then only one committed version row landing in the stricter modes
  - the committed HTML dashboard links the summary card, final-state diff, and timeline SVGs from one recruiter-friendly page
- the committed gallery landing page links this dashboard alongside the other scenarios so the whole lab reads like one polished portfolio artifact instead of three disconnected exports
- `repeatable_read_window.json`
  - `read-committed` lets the reader observe different values across its two reads, causing the transaction's repeatable-read assertion to fail
  - `snapshot` keeps the reader on a stable snapshot so the reader commits cleanly
  - `serializable` also gives the reader a stable snapshot, but the final optimistic validation can still abort the transaction because its read set changed before commit
  - `strict-2pl` keeps the reader stable by forcing the writer to abort on a lock conflict before the update lands
  - the SVG timelines make the mid-schedule writer commit or abort easy to spot without reading raw JSON traces
- `conference_room_booking_phantom.json`
  - both booking transactions scan the same `booking_room101_...` predicate and each sees zero rows before inserting a different reservation row
  - `read-committed` and `snapshot` both allow the double-booking because there is no direct key overlap to abort on
  - `serializable` now detects that the scanned predicate changed between snapshot and commit, so one booking aborts with a predicate-conflict explanation
  - `strict-2pl` protects the same predicate earlier by aborting a conflicting insert against the other coordinator's scan lock
  - the committed compare report and SVG timelines make the phantom anomaly visible without needing a database server

## Testing
```bash
python3 -m unittest tests.test_mvcc_isolation_lab -v
```

## Future ideas
- add richer scan payloads (for example exposing matched key previews directly to expressions) while keeping the DSL compact
- add a deadlock/waiting-mode variant that contrasts deterministic aborts with queue-based lock scheduling
- add per-scenario timeline thumbnails or key event callouts to the gallery while keeping the page static and dependency-free
