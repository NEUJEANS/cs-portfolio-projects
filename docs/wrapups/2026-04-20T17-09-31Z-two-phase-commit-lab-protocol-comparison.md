# Two-phase commit lab wrap-up

- timestamp: `2026-04-20T17:09:31Z`
- project: `two-phase-commit-lab`
- feature commit: `ea1156d` (`feat(two-phase-commit-lab): add protocol comparison mode`)

## What changed
- added a first-class `compare` CLI mode that contrasts the same scenario under plain 2PC versus an orchestrated saga and can emit both Markdown and JSON artifacts
- committed the classic blocking comparison bundle plus a second partial-delivery comparison bundle so GitHub readers can see both pure blocking and peer-assisted termination stories without running the code first
- tightened the comparison snapshot and takeaways after review so blocked-after-decision cases now show successful pre-crash decision deliveries, peers that already know the durable outcome, and any actionable termination hint
- refreshed the project README/checklists plus slice-specific research, learning, and review notes to keep the repo resumable

## Tests and reviews run
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.md --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.json`
- deterministic double-export hash check for the classic blocking comparison Markdown/JSON artifact using two fresh temp roots
- `git diff --check`
- review pass 1: split crash-truncated decision delivery details away from participant-configured missed-delivery wording in the comparison snapshot
- review pass 2: surfaced actionable termination hints directly in the comparison artifact for blocked-after-decision cases
- review pass 3: added a distinct peer-assisted-blocking takeaway so partial-delivery incidents no longer read like generic blind waits

## Secret scan
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` → passed with 0 verified and 0 unverified secrets

## Next step
- consider a compact HTML comparison dashboard or scenario-tag grouping so the new protocol-comparison artifacts stay easy to browse as the lab grows
