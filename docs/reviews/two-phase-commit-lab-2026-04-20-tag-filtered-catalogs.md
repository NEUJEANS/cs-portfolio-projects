# Two-phase commit lab review — 2026-04-20 — tag-filtered catalogs slice

## Pass 1 — filtered subset output risked overwriting the main incident dashboard
- Re-read the `catalog` write path with the new filtered-subset workflow in mind.
- Issue found: if a filtered catalog is written into the same artifact directory as the canonical `scenario_catalog.md`, reusing the fixed `incident_response_dashboard.html` filename would silently overwrite the main dashboard.
- Fix: added `_catalog_incident_dashboard_path(...)` so the canonical full bundle keeps `incident_response_dashboard.html`, while filtered catalogs write a stem-specific dashboard such as `peer_assisted_scenarios_catalog_incident_response_dashboard.html`.

## Pass 2 — CLI tag filters needed to match scenario-tag normalization exactly
- Re-read the scenario-tag schema and the new CLI filter flow together.
- Issue found: a separate ad-hoc CLI normalization path would drift from the scenario validator and make tags like `peer assisted commit` vs `peer-assisted-commit` behave inconsistently.
- Fix: reused `_normalize_scenario_tags(...)` for `--include-tag` handling, then added explicit any-match and all-tags regression coverage.

## Pass 3 — subset bundles needed real artifact-level verification, not just unit tests
- Re-read the rendered subset catalog and dashboard from a recruiter/browser perspective.
- Issue found: unit tests alone did not prove the committed subset artifacts stayed deterministic or that every Markdown link resolved from the final checked-in bundle.
- Fix: added a real filtered-catalog CLI smoke test, ran deterministic double-export hashing for the filtered catalog and dashboard, and verified every Markdown link emitted by `peer_assisted_scenarios_catalog.md` resolves on disk.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --include-tag peer-assisted-commit --include-tag peer-assisted-abort --markdown-out docs/artifacts/two-phase-commit-lab/peer_assisted_scenarios_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- deterministic double-export hash check for `peer_assisted_scenarios_catalog.md` and `peer_assisted_scenarios_catalog_incident_response_dashboard.html`
- Markdown link-existence verification for every link emitted in `docs/artifacts/two-phase-commit-lab/peer_assisted_scenarios_catalog.md`
- `git diff --check`
