# library-manager-sqlite

## Overview
A SQLite-backed CLI for managing a small library catalog with real circulation flows: add books, search the catalog, check books out to borrowers, return them, and report overdue loans.

## Why it is portfolio-worthy
- shows persistent state management with SQLite
- demonstrates schema migration for an evolving project
- models real state transitions instead of simple CRUD only
- includes query-driven features such as search and overdue reporting
- keeps the stack lightweight and easy to run locally

## Stack
- Python 3
- SQLite via the standard library

## Features
- add books with title and author metadata
- search by title or author
- checkout with borrower name and configurable loan duration
- return flow that clears loan metadata
- overdue report relative to today or a supplied date
- automated tests for core workflows and CLI behavior

## Usage
```bash
python3 library_manager.py --db library.db add "Clean Code" "Robert C. Martin"
python3 library_manager.py --db library.db checkout 1 "Alice" --days 21
python3 library_manager.py --db library.db list --query martin
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
