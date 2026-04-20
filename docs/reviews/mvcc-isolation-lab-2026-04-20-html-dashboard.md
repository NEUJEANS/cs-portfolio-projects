# MVCC isolation lab review — 2026-04-20 — HTML dashboard slice

## Pass 1 — abort-cause clarity
- Re-read the repeatable-read dashboard summary against the scenario semantics.
- Issue found: the page highlighted optimistic vs lock abort styles, but the `read-committed` reader abort came from the scenario assertion and was easy to mentally bucket as another concurrency-control conflict.
- Fix: added an `Abort causes` summary card plus per-transaction `Abort class` labels so assertion-driven aborts are separated from validation/lock conflicts.

## Pass 2 — missing top-level scenario context
- Re-read the dashboard as if landing directly from a portfolio page without first opening the README.
- Issue found: the page jumped straight from the lede into per-mode cards, which made the scale of the schedule less obvious than it should be.
- Fix: added hero fact chips and a `Scenario footprint` summary card covering transaction count, schedule ticks, and invariant count.

## Pass 3 — static-page interaction affordances
- Re-read the generated HTML from a keyboard/accessibility perspective instead of only visually.
- Issue found: companion links relied mostly on color, with weak affordance for hover/focus on a static page.
- Fix: added underline/focus-visible styling and outline treatment for hero and companion links.

## Final verification
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab --html-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_dashboard.html`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab --html-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_dashboard.html`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/conference_room_booking_phantom.json --markdown-out docs/artifacts/mvcc-isolation-lab/conference_room_booking_phantom_compare.md --timeline-svg-dir docs/artifacts/mvcc-isolation-lab --html-out docs/artifacts/mvcc-isolation-lab/conference_room_booking_phantom_dashboard.html`
- deterministic double-export hash check for the three `*_dashboard.html` files
- `git diff --check`
