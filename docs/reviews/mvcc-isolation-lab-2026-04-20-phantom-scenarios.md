# MVCC isolation lab review — 2026-04-20 — phantom scenario slice

## Pass 1 — comparison report context
- Re-read the generated Markdown artifacts from the perspective of a recruiter landing directly on the file.
- Issue found: the comparison report jumped straight from the heading into the table, so readers lost the scenario story unless they also opened the JSON scenario file.
- Fix: `render_compare_markdown(...)` now includes the scenario description under the heading, and the export test was tightened to keep that context present.

## Pass 2 — README / DSL documentation drift
- Re-read the project README against the implemented CLI/DSL surface.
- Issue found: the new `scan` step, `count_prefix(...)` helper, and phantom-booking scenario were not documented, which would make the committed artifacts look like magic.
- Fix: updated the README features, step-type reference, committed-sample section, and future-ideas list so the new predicate-validation slice is explainable and resumable.

## Pass 3 — resumability / next-step hygiene
- Re-read the project and root checklists plus artifact inventory from the perspective of the next cron run.
- Issue found: the main checklists still showed phantom scenarios as unfinished even though the code/artifacts existed locally, which would make the next run pick the wrong follow-up.
- Fix: marked the phantom milestone complete, added a slice-specific checklist, and kept the next high-value follow-up focused on a contrasting lock-based mode rather than reopening the same work.

## Final verification
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py validate projects/mvcc-isolation-lab/conference_room_booking_phantom.json`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/conference_room_booking_phantom.json --markdown-out docs/artifacts/mvcc-isolation-lab/conference_room_booking_phantom_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab`
- `git diff --check`
