# library-manager-sqlite

## Overview
A SQLite-backed CLI for managing a small library catalog with real circulation flows: add books, search the catalog, check books out to borrowers, return them, and report overdue loans.

## Why it is portfolio-worthy
- shows persistent state management with SQLite
- demonstrates schema migration for an evolving project
- models real state transitions instead of simple CRUD only
- keeps an auditable borrower and loan-history trail instead of only the current checked-out row state
- now includes ranked SQLite FTS5 search with prefix and phrase-query support
- exposes history and circulation analytics that are easy to demo in interviews
- keeps the stack lightweight and easy to run locally

## Stack
- Python 3
- SQLite via the standard library, including FTS5 when available

## Features
- add books with title and author metadata
- search by title or author using substring matching or ranked full-text search
- full-text search supports prefix-style free-text queries like `distr tanen` and advanced phrase queries like `"distributed systems"`
- `--search-mode auto` prefers FTS when available and safely falls back to substring matching on SQLite builds without FTS5
- checkout with borrower name and configurable loan duration
- return flow that clears the current book-row loan metadata while preserving an audit trail in a dedicated `loans` table
- borrower records are normalized into their own table so repeat borrowers can be summarized cleanly
- `history` shows active, overdue, or returned circulation records with lateness context
- `stats` summarizes total loans, overdue activity, return-time averages, and top borrowers
- migration path for older databases plus automatic backfill of the search index and any still-active legacy checkouts
- automated tests for core workflows, migration safety, and CLI behavior

## Usage
```bash
python3 library_manager.py --db library.db add "Clean Code" "Robert C. Martin"
python3 library_manager.py --db library.db checkout 1 "Alice" --days 21
python3 library_manager.py --db library.db list --query martin --search-mode keyword
python3 library_manager.py --db library.db list --query 'distr tanen' --search-mode auto
python3 library_manager.py --db library.db list --query '"distributed systems"' --search-mode fts --limit 5
python3 library_manager.py --db library.db overdue --date 2026-04-30
python3 library_manager.py --db library.db history --status overdue --date 2026-04-30
python3 library_manager.py --db library.db stats --date 2026-04-30 --top 5
python3 library_manager.py --db library.db return 1
```

## Test
```bash
python3 -m unittest test_library_manager.py
```

## Future Improvements
- support borrower borrowing limits or policy rules
- add import/export for seed catalogs
- package the project as an installable CLI
- add small HTML report exports for circulation trends and overdue snapshots
