# Two-phase commit lab review — 2026-04-20 — catalog slice

## Pass 1 — missing scenario context in the landing page
- Read the generated catalog as if a recruiter landed there first without opening any per-scenario report.
- Issue found: the snapshot section listed source path and protocol outcome, but it did not restate each scenario description, so the business/story framing was weaker than the detailed reports.
- Fix: added a `description` line for every snapshot entry so the catalog stands on its own before the reader clicks deeper.

## Pass 2 — blocked-vs-decided comparison clarity
- Re-read the comparison table specifically for the crash cases.
- Issue found: the table exposed durable-decision presence, but it did not show the effective decision value directly, which made the blocked-before-decision case less scannable than it should be.
- Fix: added an explicit `Decision` column alongside `Outcome` and `Durable decision` so readers can distinguish `blocked + none` from completed `commit` or `abort` runs at a glance.

## Pass 3 — renderer maintenance fragility
- Audited the catalog renderer for assumptions that could break future copy edits.
- Issue found: the snapshot summary was pulling `result.takeaways[-2]`, which depended on the current ordering of takeaway strings instead of the meaning of the takeaway itself.
- Fix: added `_primary_takeaway(...)` so the catalog chooses the blocking reason when present, otherwise the protocol-summary takeaway, with a safe fallback.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py catalog projects/two-phase-commit-lab --markdown-out docs/artifacts/two-phase-commit-lab/scenario_catalog.md --report-dir docs/artifacts/two-phase-commit-lab`
- deterministic double-export hash check for `scenario_catalog.md` using two fresh temp roots with the same `reports/` layout
- `git diff --check`
