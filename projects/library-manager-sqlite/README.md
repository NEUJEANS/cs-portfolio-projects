# library-manager-sqlite

## Overview
A SQLite-backed CLI for managing a small library catalog with real circulation flows: add books, search the catalog, check books out to borrowers, return them, and report overdue loans.

## Why it is portfolio-worthy
- shows persistent state management with SQLite
- demonstrates schema migration for an evolving project
- models real state transitions instead of simple CRUD only
- now includes ranked SQLite FTS5 search with prefix and phrase-query support
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
- return flow that clears loan metadata
- overdue report relative to today or a supplied date
- migration path for older databases plus automatic FTS index backfill for existing catalogs
- automated tests for core workflows, migration safety, and CLI behavior

## Usage
```bash
python3 library_manager.py --db library.db add "Clean Code" "Robert C. Martin"
python3 library_manager.py --db library.db checkout 1 "Alice" --days 21
python3 library_manager.py --db library.db list --query martin --search-mode keyword
python3 library_manager.py --db library.db list --query 'distr tanen' --search-mode auto
python3 library_manager.py --db library.db list --query '"distributed systems"' --search-mode fts --limit 5
python3 library_manager.py --db library.db overdue --date 2026-04-30
python3 library_manager.py --db library.db return 1
```

## Test
```bash
python3 -m unittest test_library_manager.py
```

## Future Improvements
- separate loan history into its own table for auditability
- support borrower records and borrowing limits
- add import/export for seed catalogs
- package the project as an installable CLI
