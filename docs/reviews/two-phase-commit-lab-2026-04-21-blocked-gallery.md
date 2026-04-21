# Review log — two-phase-commit-lab blocked timeline gallery slice — 2026-04-21

## Pass 1 — gallery navigation review
- Reviewed the first gallery card interaction path against the slice goal.
- Issue found: clicking the cover opened the raw PNG file, which is less useful than the full walkthrough.
- Fix: changed the cover click target to prefer timeline HTML, then SVG, and only fall back to PNG when no richer artifact exists.

## Pass 2 — card copy review
- Reviewed the gallery card summary copy for recruiter readability.
- Issue found: the primary takeaway sentence sometimes started lowercase because it came straight from the internal summary helper.
- Fix: normalized the gallery callout text into sentence case so each card reads like polished user-facing copy.

## Pass 3 — blocked-state labeling review
- Reviewed the gallery badges and quick-scan semantics for the fully blocked no-decision case.
- Issue found: the first draft showed a `NONE` decision pill, which felt too raw and implementation-flavored.
- Fix: changed the no-decision label to `UNDECIDED`, which communicates the blocked state more clearly to recruiters and interviewers.

## Pass 4 — generated artifact hygiene review
- Ran `git diff --check` on the regenerated artifacts.
- Issue found: zero-blocked preset dashboards emitted a blank indented line inside the hero link container, which produced trailing-whitespace failures.
- Fix: switched the dashboard renderer to build hero links by joining only the links that actually exist, then regenerated all catalog/dashboard/gallery bundles.

## Validation run after fixes
- `python3 tests/test_two_phase_commit_lab.py -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- regenerated the preset bundles under `docs/artifacts/two-phase-commit-lab/` so the new gallery artifacts and cross-links are committed consistently
- `git diff --check`
