# MVCC isolation lab scenario gallery

A recruiter-friendly landing page for the committed MVCC scenarios, with per-scenario dashboards, Markdown comparisons, and timeline SVGs.

Regenerate with `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py catalog <scenario-dir> --output-dir <artifact-dir>` when you want to refresh the full bundle.

| Scenario | Txs | Ticks | Safe modes | Anomaly modes | Aborted txs | Dashboard | Markdown |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| [Conference room booking phantom](conference_room_booking_phantom_dashboard.html) | 2 | 6 | 2 | 2 | 2 | [dashboard](conference_room_booking_phantom_dashboard.html) | [compare](conference_room_booking_phantom_compare.md) |
| [Doctor on-call write skew](doctor_on_call_dashboard.html) | 2 | 8 | 2 | 2 | 2 | [dashboard](doctor_on_call_dashboard.html) | [compare](doctor_on_call_compare.md) |
| [Repeatable read window](repeatable_read_window_dashboard.html) | 2 | 5 | 4 | 0 | 3 | [dashboard](repeatable_read_window_dashboard.html) | [compare](repeatable_read_window_compare.md) |

## [Conference room booking phantom](conference_room_booking_phantom_dashboard.html)

Two coordinators each scan for an open room slot before inserting a separate reservation row. Key-based conflicts miss the shared predicate, so only serializable predicate validation should stop the double-booking anomaly.

- scenario: `conference_room_booking_phantom.json`
- footprint: 2 transactions, 6 schedule ticks, 1 invariant
- outcomes: 2 safe modes, 2 anomaly-visible modes, 2 aborted transactions across all modes
- companion artifacts: [Markdown comparison](conference_room_booking_phantom_compare.md)
- timelines: [read-committed](conference_room_booking_phantom_read_committed_timeline.svg), [snapshot](conference_room_booking_phantom_snapshot_timeline.svg), [serializable](conference_room_booking_phantom_serializable_timeline.svg), [strict-2pl](conference_room_booking_phantom_strict_2pl_timeline.svg)

## [Doctor on-call write skew](doctor_on_call_dashboard.html)

Two doctors each see coverage in their snapshot and independently sign off, illustrating write skew under snapshot isolation.

- scenario: `doctor_on_call.json`
- footprint: 2 transactions, 8 schedule ticks, 1 invariant
- outcomes: 2 safe modes, 2 anomaly-visible modes, 2 aborted transactions across all modes
- companion artifacts: [Markdown comparison](doctor_on_call_compare.md)
- timelines: [read-committed](doctor_on_call_read_committed_timeline.svg), [snapshot](doctor_on_call_snapshot_timeline.svg), [serializable](doctor_on_call_serializable_timeline.svg), [strict-2pl](doctor_on_call_strict_2pl_timeline.svg)

## [Repeatable read window](repeatable_read_window_dashboard.html)

A long-running reader observes a value twice while a concurrent writer increments it in the middle of the schedule.

- scenario: `repeatable_read_window.json`
- footprint: 2 transactions, 5 schedule ticks, 1 invariant
- outcomes: 4 safe modes, 0 anomaly-visible modes, 3 aborted transactions across all modes
- companion artifacts: [Markdown comparison](repeatable_read_window_compare.md)
- timelines: [read-committed](repeatable_read_window_read_committed_timeline.svg), [snapshot](repeatable_read_window_snapshot_timeline.svg), [serializable](repeatable_read_window_serializable_timeline.svg), [strict-2pl](repeatable_read_window_strict_2pl_timeline.svg)
