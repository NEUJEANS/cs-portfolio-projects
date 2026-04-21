# Two-phase commit lab review — 2026-04-21 — 3PC comparison slice

## Pass 1 — saga hero chip used a warning tone even on success
- Re-ran the compare dashboard on the happy-path scenario instead of only the blocked crash cases.
- Issue found: the hero meta chip for saga was hardcoded to the warning color, so `eventual-commit` still looked like a failure state.
- Fix: switched the saga chip to use the same outcome-tone helper as the 2PC and 3PC chips.

## Pass 2 — 3PC timeout wording overclaimed production realism
- Re-read the blocked comparison Markdown as if an interviewer were asking whether the lab was simulating real partition-safe 3PC behavior.
- Issue found: the timeout-assisted commit/abort copy was slightly too absolute and could sound like production-safe recovery instead of a textbook bounded-delay story.
- Fix: tightened the 3PC recovery and participant wording to explicitly say `textbook bounded-delay model` where the comparison leans on timeout recovery.

## Pass 3 — compare UX and docs needed consistency after the extra protocol landed
- Re-read the compare CLI help, README comparison section, and regenerated artifacts together.
- Issue found: the project needed the comparison feature wording updated everywhere so the new 3PC layer did not look like an undocumented hidden behavior.
- Fix: updated the compare command help, README feature/usage text, and checklist history, then regenerated the committed comparison artifacts and catalog bundles.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --bundle-preset incident-review --markdown-out docs/artifacts/two-phase-commit-lab/incident_review_scenarios_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --bundle-preset recovery-story --markdown-out docs/artifacts/two-phase-commit-lab/recovery_story_scenarios_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --bundle-preset peer-assisted --markdown-out docs/artifacts/two-phase-commit-lab/peer_assisted_scenarios_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- happy-path compare dashboard spot-check for dynamic success-toned saga chip
- `git diff --check`
