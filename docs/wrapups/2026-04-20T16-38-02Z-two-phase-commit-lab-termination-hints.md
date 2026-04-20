# Two-phase commit lab wrap-up

- timestamp: `2026-04-20T16:38:02Z`
- project: `two-phase-commit-lab`
- feature commit: `703e059` (`feat(two-phase-commit-lab): add termination protocol hints`)

## What changed
- added a new `coordinator_crash_partial_commit_delivery.json` scenario where one participant learns durable `COMMIT` before the coordinator crashes
- extended the simulator with termination-protocol guidance, partial second-phase delivery handling, and explicit reporting for configured vs successful pre-crash decision deliveries
- refreshed the README, project checklist, repo checklist, tests, per-scenario Markdown artifacts, and the scenario catalog to surface the new blocked-case story

## Tests and reviews run
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py run projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --json`
- `git diff --check`
- review pass 1: logic review of the crash/termination flow and validation rules
- review pass 2: added a regression test so missed pre-crash deliveries do not get miscounted as successful
- review pass 3: artifact/readability review, including a singular/plural wording fix in the takeaways
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add a 2PC vs 3PC or saga comparison mode so the portfolio can contrast blocking atomic commit with alternative coordination strategies
