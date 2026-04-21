# library-manager-sqlite

## Overview
A SQLite-backed CLI for managing a small library catalog with real circulation flows: add books, tag them by genre, search the catalog, check books out to borrowers, return them, and report overdue loans.

## Why it is portfolio-worthy
- shows persistent state management with SQLite
- demonstrates schema migration for an evolving project
- models real state transitions instead of simple CRUD only
- keeps an auditable borrower and loan-history trail instead of only the current checked-out row state
- now includes ranked SQLite FTS5 search with prefix and phrase-query support
- now includes genre metadata plus genre-level trend exports so the analytics pack can tell subject-level circulation stories
- exposes history, circulation analytics, and recruiter-friendly dashboard exports that are easy to demo in interviews
- keeps the stack lightweight and easy to run locally

## Stack
- Python 3
- SQLite via the standard library, including FTS5 when available

## Features
- add books with title and author metadata
- optional genre metadata on each book, with migration-safe defaults for older databases
- search by title or author using substring matching or ranked full-text search
- full-text search supports prefix-style free-text queries like `distr tanen` and advanced phrase queries like `"distributed systems"`
- `--search-mode auto` prefers FTS when available and safely falls back to substring matching on SQLite builds without FTS5
- checkout with borrower name and configurable loan duration
- return flow that clears the current book-row loan metadata while preserving an audit trail in a dedicated `loans` table
- borrower records are normalized into their own table so repeat borrowers can be summarized cleanly
- `history` shows active, overdue, or returned circulation records with lateness context
- `stats` summarizes total loans, overdue activity, return-time averages, and top borrowers
- `dashboard` exports Markdown and HTML circulation snapshots with accessible tables, status pills, and machine-readable timestamps
- `trends` exports daily circulation analytics as chart-friendly CSV plus an accessible SVG small-multiples report for portfolio screenshots
- `borrower-trends` exports top-borrower daily breakdowns as CSV plus a recruiter-friendly SVG cohort dashboard
- `genre-trends` exports top-genre daily breakdowns as CSV plus a recruiter-friendly SVG cohort dashboard
- `genre-heatmap` exports a one-glance genre/day activity heatmap as CSV plus an accessible SVG summary for portfolio screenshots
- dashboard snapshots respect the selected `--date`, so historical exports do not leak future checkouts or returns into earlier views
- trend exports respect the requested date range so historical charts stay stable and repeatable in committed artifacts
- borrower trend exports focus on the top borrower cohorts touching the selected range, so recruiter demos stay readable even as history grows
- genre trend exports focus on the busiest genres touching the selected range, so recruiter demos can explain subject-level usage without opening SQLite manually
- migration path for older databases plus automatic backfill of the search index and any still-active legacy checkouts
- automated tests for core workflows, migration safety, dashboard and trend rendering, and CLI behavior

## Usage
```bash
python3 library_manager.py --db library.db add "Clean Code" "Robert C. Martin" --genre "Software Engineering"
python3 library_manager.py --db library.db checkout 1 "Alice" --days 21
python3 library_manager.py --db library.db list --query martin --search-mode keyword
python3 library_manager.py --db library.db list --query 'distr tanen' --search-mode auto
python3 library_manager.py --db library.db list --query '"distributed systems"' --search-mode fts --limit 5
python3 library_manager.py --db library.db overdue --date 2026-04-30
python3 library_manager.py --db library.db history --status overdue --date 2026-04-30
python3 library_manager.py --db library.db stats --date 2026-04-30 --top 5
python3 library_manager.py --db library.db trends --start-date 2026-04-01 --end-date 2026-04-30 \
  --csv-out ../../docs/artifacts/library-manager-sqlite/sample_circulation_trends.csv \
  --svg-out ../../docs/artifacts/library-manager-sqlite/sample_circulation_trends.svg \
  --generated-at 2026-04-30T12:00:00Z
python3 library_manager.py --db library.db borrower-trends --start-date 2026-04-01 --end-date 2026-04-30 \
  --top 4 \
  --csv-out ../../docs/artifacts/library-manager-sqlite/sample_borrower_trends.csv \
  --svg-out ../../docs/artifacts/library-manager-sqlite/sample_borrower_trends.svg \
  --generated-at 2026-04-30T12:00:00Z
python3 library_manager.py --db library.db genre-trends --start-date 2026-04-01 --end-date 2026-04-30 \
  --top 4 \
  --csv-out ../../docs/artifacts/library-manager-sqlite/sample_genre_trends.csv \
  --svg-out ../../docs/artifacts/library-manager-sqlite/sample_genre_trends.svg \
  --generated-at 2026-04-30T12:00:00Z
python3 library_manager.py --db library.db genre-heatmap --start-date 2026-04-01 --end-date 2026-04-30 \
  --top 4 \
  --csv-out ../../docs/artifacts/library-manager-sqlite/sample_genre_heatmap.csv \
  --svg-out ../../docs/artifacts/library-manager-sqlite/sample_genre_heatmap.svg \
  --generated-at 2026-04-30T12:00:00Z
python3 library_manager.py --db library.db dashboard --date 2026-04-30 \
  --markdown-out ../../docs/artifacts/library-manager-sqlite/sample_circulation_dashboard.md \
  --html-out ../../docs/artifacts/library-manager-sqlite/sample_circulation_dashboard.html \
  --generated-at 2026-04-30T12:00:00Z
python3 library_manager.py --db library.db return 1
```

## Portfolio artifacts
- sample Markdown snapshot: `docs/artifacts/library-manager-sqlite/sample_circulation_dashboard.md`
- sample HTML snapshot: `docs/artifacts/library-manager-sqlite/sample_circulation_dashboard.html`
- sample trends CSV: `docs/artifacts/library-manager-sqlite/sample_circulation_trends.csv`
- sample trends SVG: `docs/artifacts/library-manager-sqlite/sample_circulation_trends.svg`
- sample borrower trends CSV: `docs/artifacts/library-manager-sqlite/sample_borrower_trends.csv`
- sample borrower trends SVG: `docs/artifacts/library-manager-sqlite/sample_borrower_trends.svg`
- sample genre trends CSV: `docs/artifacts/library-manager-sqlite/sample_genre_trends.csv`
- sample genre trends SVG: `docs/artifacts/library-manager-sqlite/sample_genre_trends.svg`
- sample genre heatmap CSV: `docs/artifacts/library-manager-sqlite/sample_genre_heatmap.csv`
- sample genre heatmap SVG: `docs/artifacts/library-manager-sqlite/sample_genre_heatmap.svg`

## Test
```bash
python3 -m unittest test_library_manager.py
```

## Future Improvements
- support borrower borrowing limits or policy rules
- add import/export for seed catalogs
- package the project as an installable CLI
- add a stacked-share export so the subject mix can also be shown as a compact composition view alongside the new heatmap
