# Two-phase commit lab review — 2026-04-20 — catalog cross-links slice

## Pass 1 — companion-artifact lookup risked dead links in fresh temp outputs
- Re-read the new catalog discovery path with the existing temp-dir catalog tests in mind.
- Issue found: companion links must not appear just because the naming convention exists conceptually; they should appear only when the files are actually present.
- Fix: added `_relative_artifact_path(...)` so catalog entries only expose links for files that exist on disk.

## Pass 2 — table-only links made the snapshot section feel stale
- Re-read the rendered catalog from a recruiter perspective starting at the scenario snapshots instead of the comparison table.
- Issue found: the table had the useful deep links, but the snapshot section still looked like report-only navigation.
- Fix: added a `related artifacts` line per snapshot that lists report, compare HTML/Markdown, and termination Markdown companions when present.

## Pass 3 — regressions needed explicit companion-discovery coverage
- Re-read the test suite after the first implementation pass.
- Issue found: the catalog tests covered report generation, but not discovery of pre-existing comparison/termination companions.
- Fix: added a focused temp-dir test that seeds fake comparison/termination artifacts and verifies the rendered catalog links/counts.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- deterministic double-export hash check for `scenario_catalog.md` using two fresh temp roots with regenerated `reports/` directories
- link-existence verification for every Markdown link emitted in `docs/artifacts/two-phase-commit-lab/scenario_catalog.md`
- `git diff --check`
