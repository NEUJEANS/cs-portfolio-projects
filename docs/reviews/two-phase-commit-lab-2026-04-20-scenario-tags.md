# Two-phase commit lab review — 2026-04-20 — scenario tags slice

## Pass 1 — tags were not visible enough in per-scenario artifacts
- Re-read the generated report and protocol-comparison artifact flow as if a recruiter landed on a single file instead of the catalog.
- Issue found: adding tags only to the scenario JSON would make the new metadata effectively invisible unless someone opened the source files directly.
- Fix: surfaced normalized scenario tags in Markdown reports, comparison Markdown, comparison HTML snapshot cards, comparison JSON snapshots, and the main catalog table/snapshots.

## Pass 2 — raw tag grouping made the catalog noisier than it needed to be
- Re-read the regenerated catalog after the first implementation pass.
- Issue found: every singleton tag became its own section, which diluted the higher-signal grouping value and made the theme section feel too busy.
- Fix: kept all tags on each scenario row, but curated the top-level theme groups so they only show repeated tags or explicitly high-value portfolio themes like `participant-reconnect`, `recovery`, `peer-assisted-commit`, and `peer-assisted-abort`.

## Pass 3 — tag input needed normalization and duplicate guards
- Re-read the scenario schema and test suite from the perspective of future resumable edits.
- Issue found: free-form tags would drift (`Peer Assisted Commit`, `peer_assisted_commit`, `peer-assisted-commit`) and make the catalog grouping brittle.
- Fix: normalized tags to lowercase kebab-case, rejected duplicates after normalization, added regression tests for both behaviors, and committed tags into every sample scenario JSON.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_before_decision.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_before_decision_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py compare projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --markdown-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.md --html-out docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.html --json > docs/artifacts/two-phase-commit-lab/coordinator_crash_partial_commit_delivery_protocol_compare.json`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `git diff --check`
