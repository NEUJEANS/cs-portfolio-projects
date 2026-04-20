# Two-phase commit lab review — 2026-04-20 — HTML comparison dashboard slice

## Pass 1 — informed-peer summary text had grammar drift
- Re-read the generated dashboards for both zero-informed-peer and one-informed-peer scenarios.
- Issue found: the summary card said `none yet already know` in the classic blocked case and `inventory already know` in the peer-visible case.
- Fix: generated the description through count-aware wording so zero peers reads naturally and singular/plural agreement stays correct.

## Pass 2 — informed peers were easy to miss in the snapshot grid
- Re-read the dashboard as if landing in the middle of the page rather than starting from the hero.
- Issue found: the snapshot grid showed crash point and voter mix, but not an explicit row for which participants already learned the final 2PC decision.
- Fix: added a dedicated snapshot row for the informed-participant list so the peer-assisted blocking story stays visible outside the summary cards.

## Pass 3 — pre-crash delivery count looked misleading in non-post-log crashes
- Re-read the classic `before-decision` dashboard after seeing the partial-delivery dashboard.
- Issue found: `Successful pre-crash decision deliveries: 0` looked like a failed post-log fanout rather than an inapplicable field.
- Fix: switched the row to `n/a (no post-log crash)` unless the scenario actually crashes after the durable decision log.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.json`
- deterministic double-export hash check for the partial-delivery HTML artifact using two fresh temp roots
- `git diff --check`
