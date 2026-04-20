# Wrap-up — MVCC isolation lab phantom scenario slice

- **Timestamp:** 2026-04-20T12:45:54Z
- **Project:** `mvcc-isolation-lab`
- **Feature commit:** `c5ff5dd` (`feat(mvcc-isolation-lab): add phantom predicate scenarios`)

## What changed
- extended the MVCC lab with predicate-style `scan` steps plus serializable predicate-conflict validation so the simulator can model range/phantom anomalies instead of only direct key overlap
- added a new `conference_room_booking_phantom.json` scenario where two booking transactions scan the same room-slot predicate, then write disjoint reservation rows that double-book under `read-committed` and `snapshot`
- committed a new Markdown comparison artifact plus three SVG timelines for the phantom scenario and refreshed the existing doctor/repeatable comparison reports so every report now includes scenario context under the heading
- updated the project/root checklists, README, research note, refresh/self-test note, and a dedicated 3-pass review log so the slice is resumable and interviewer-friendly
- tightened regression coverage around scan validation, phantom outcomes across all three isolation levels, JSON trace contents, and recruiter-facing compare-markdown context

## Tests and reviews run
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v` (`20/20`)
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py validate projects/mvcc-isolation-lab/conference_room_booking_phantom.json`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/conference_room_booking_phantom.json --markdown-out docs/artifacts/mvcc-isolation-lab/conference_room_booking_phantom_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- deterministic double-export hash check for the phantom compare Markdown + three timeline SVGs
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review log: `docs/reviews/mvcc-isolation-lab-2026-04-20-phantom-scenarios.md`

## Next step
- add a contrasting lock-based serializable mode (for example strict 2PL / predicate-lock teaching flow) so the repo can compare optimistic validation versus blocking-based anomaly prevention on the same scenarios
