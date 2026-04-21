# Library manager SQLite review — 2026-04-21 — loan-history + analytics slice

## Pass 1 — legacy-migration integrity review
- Reviewed the new normalized `borrowers` / `loans` flow against older databases that only have the legacy `books.borrower`, `checked_out_at`, and `due_date` fields.
- Issue found: a legacy checked-out row could be returned before a normalized `loans` row existed, which would clear the book state but lose the audit trail.
- Fix: added active-loan backfill during initialization and a defensive `_reconstruct_active_loan(...)` path in `return_book(...)` so old databases still preserve an auditable loan row on return.

## Pass 2 — CLI analytics output review
- Ran real `stats` smoke commands against both active-only and mixed returned/active datasets.
- Issue found: when there were no completed returns yet, the CLI printed `actual return 0.0d`, which looked like a measured zero-day average instead of "not available yet."
- Fix: changed analytics formatting so missing averages render as `n/a`, while genuine same-day returns still show `0.0d`.

## Pass 3 — resumability/docs review
- Reviewed the slice as if the next cron run only had the project README and checklist for context.
- Issue found: the docs still described the project mostly as current-state circulation plus search, so the new normalized borrower/history story and CLI surfaces were easy to miss.
- Fix: updated the README feature list, usage examples, and future follow-up item, and expanded `docs/checklists/library-manager-sqlite.md` so the completed audit-trail slice and next dashboard follow-up are explicit.

## Final verification
- `python3 -m py_compile library_manager.py test_library_manager.py`
- `python3 -m unittest -v test_library_manager.py` (`11/11`)
- real CLI smoke for `add`, `checkout`, `return`, `history`, and `stats`
- `git diff --check`
