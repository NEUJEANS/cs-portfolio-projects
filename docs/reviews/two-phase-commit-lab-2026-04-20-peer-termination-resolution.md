# Two-phase commit lab review — 2026-04-20 — peer termination resolution slice

## Pass 1 — artifact title was inconsistent with the README language
- Re-read the generated termination Markdown artifacts after the first implementation pass.
- Issue found: the artifacts used the shorter phrase `peer termination resolution`, while the README and feature description used `peer-to-peer termination`.
- Fix: renamed the Markdown heading to `peer-to-peer termination resolution` and updated the regression test so the artifact language stays consistent.

## Pass 2 — project structure docs did not clearly advertise the new artifact family
- Re-read `projects/two-phase-commit-lab/README.md` as if browsing the repo on GitHub without prior context.
- Issue found: the new committed termination artifacts existed in `docs/artifacts/two-phase-commit-lab/`, but the project-structure bullet only mentioned reports, the catalog, and protocol-comparison artifacts.
- Fix: updated the README overview, feature list, project-structure section, usage examples, and committed-samples section to explicitly include the peer-resolution workflow and artifacts.

## Pass 3 — plain CLI output hid the resolved decision on successful peer recovery
- Re-ran the new `terminate` command without `--json` to check the human-readable summary path, not just the JSON export.
- Issue found: the summary printed `peer_resolution=commit` but did not show the resolved decision explicitly, which made the compact output less useful when scanning terminal logs.
- Fix: added `resolved_decision=...` to the non-JSON summary output and covered it with a dedicated subprocess test.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py terminate projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_termination.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_termination.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py terminate projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_termination.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_termination.json`
- `git diff --check`
