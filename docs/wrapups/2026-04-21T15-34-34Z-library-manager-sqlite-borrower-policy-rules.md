# Wrap-up — 2026-04-21T15:34:34Z — library-manager-sqlite borrower policy rules

## What changed
- added persistent `circulation_policy` storage with migration-safe defaults for max active loans and overdue-checkout blocking
- enforced borrower policy during checkout with clear errors for active-loan-limit and overdue-block cases
- added a new `policy` CLI that can inspect or update the rules and export recruiter-friendly Markdown/HTML borrower-compliance snapshots
- added automated coverage for default policy behavior, policy mutation, borrower-status snapshots, report renderers, and CLI artifact flow
- generated committed sample artifacts:
  - `docs/artifacts/library-manager-sqlite/sample_policy_report.md`
  - `docs/artifacts/library-manager-sqlite/sample_policy_report.html`
- updated the project README, root checklist, slice checklist, research note, self-test note, and review log for resumability

## Validation
- `python3 -m py_compile projects/library-manager-sqlite/library_manager.py projects/library-manager-sqlite/test_library_manager.py`
- `cd projects/library-manager-sqlite && python3 -m unittest -v test_library_manager.py` (`29/29`)
- real CLI smoke test generating Markdown and HTML policy reports from a seeded temporary database
- deterministic rerun check comparing two seeded `policy` export runs byte-for-byte for both Markdown and HTML outputs
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (0 verified, 0 unknown)

## Review passes
1. fixed compatibility with an older overdue-history test by explicitly disabling the overdue block only in that fixture
2. tightened the `at-limit` classification so it only appears for borrowers who already have an active loan, and upgraded portfolio-facing status labels
3. re-ran validation, smoke exports, deterministic comparisons, and whitespace checks after the fixes

## Commit
- feature commit: `83ca390` (`feat(library-manager-sqlite): add borrower policy rules`)

## Next step
- add borrower categories or item-type-specific policy overrides so the circulation rules can vary by patron or collection
