# Two-phase commit lab review — 2026-04-20 — protocol comparison slice

## Pass 1 — snapshot wording blurred two different failure stories
- Re-read the generated comparison artifact for the partial-decision-delivery crash instead of only the classic pre-decision blocking case.
- Issue found: the snapshot only showed `missed second-phase deliveries`, which made the partial-delivery blocked case look like a generic zero-miss run even though one participant had already learned the durable decision before the crash.
- Fix: split the comparison snapshot into clearer fields for participant-configured missed deliveries, participants that already learned the final 2PC decision, and successful second-phase deliveries before the crash.

## Pass 2 — actionable termination hint was hidden in the comparison view
- Re-read the new comparison output specifically as an interviewer asking whether blocked 2PC always means blind waiting.
- Issue found: the underlying simulator already knew `COMMIT visible via inventory`, but the comparison artifact did not surface that actionable hint, so the most interesting nuance of the partial-delivery scenario was invisible.
- Fix: threaded `termination_hint_summary` into the comparison snapshot and interview takeaways so the comparison now says when a prepared participant can safely ask an informed peer.

## Pass 3 — takeaways did not clearly separate pure blocking from peer-assisted blocking
- Re-read the final takeaways across the classic blocked case and the partial-delivery blocked case.
- Issue found: both scenarios ended with nearly the same generic blocking takeaway, which flattened an important operational distinction.
- Fix: added a specific takeaway when pre-crash decision deliveries exist, calling out that the incident becomes a peer-assisted response story rather than pure blind waiting.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.json`
- deterministic double-export hash check for the classic blocking comparison Markdown artifact using two fresh temp roots
- `git diff --check`
