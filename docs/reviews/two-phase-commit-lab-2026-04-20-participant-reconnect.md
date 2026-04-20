# Two-phase commit lab review — 2026-04-20 — participant reconnect slice

## Pass 1 — invalid missed-delivery configs
- Re-read the scenario schema against the simulator state machine instead of only the happy-path reconnect sample.
- Issue found: validation allowed `second_phase_delivery: "miss"` on non-`commit` voters even though aborting/timed-out participants never reach PREPARED or receive a meaningful second-phase delivery.
- Fix: tightened validation so missed second-phase delivery is only allowed for `vote: "commit"`, and added a regression test for the invalid abort+miss case.

## Pass 2 — noisy catalog cells for non-reconnect scenarios
- Re-read the generated catalog comparison table and snapshots as a recruiter browsing across all scenarios.
- Issue found: scenarios without any missed second-phase delivery showed reconnect fields as `0/0`, which looked more like a formatting artifact than a meaningful protocol signal.
- Fix: changed the comparison table and snapshot copy to render `-` plus an explanatory note when no participant missed the first second-phase delivery.

## Pass 3 — reconnect story was buried behind generic commit copy
- Re-read the reconnect scenario snapshot and report takeaways to check whether the new slice was actually visible without opening the source.
- Issue found: the catalog's `why it matters` line still preferred the generic commit takeaway, so the reconnect scenario did not foreground its distinguishing behavior; the takeaway wording also used awkward plural grammar for singular counts.
- Fix: prioritized reconnect-specific takeaways in `_primary_takeaway(...)` and added `_count_phrase(...)` so the generated report/catalog now say `1 participant ... 1 participant ...` instead of `1 participants`.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py run projects/two-phase-commit-lab/participant_reconnect_commit.json --markdown-out docs/artifacts/two-phase-commit-lab/participant_reconnect_commit_report.md --json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- deterministic double-export hash check for `scenario_catalog.md` using two fresh temp roots with the same `reports/` layout
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py validate projects/two-phase-commit-lab/participant_reconnect_commit.json`
- `git diff --check`
