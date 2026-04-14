# Library Manager Upgrade Research

Date: 2026-04-14

## Goal
Upgrade the existing SQLite library manager from a minimal add/list/checkout toy into a stronger portfolio slice with real circulation workflows.

## Brief findings
Common library circulation capabilities that add practical value without making the project too large:
- checkout should record who borrowed an item
- loans should have a due date
- returns should restore availability and clear loan metadata
- users should be able to search the catalog
- overdue reporting is a natural query-driven feature for a SQLite-backed project

## Planned slice
Implement a circulation-focused upgrade:
1. extend schema with borrower, checked_out_at, and due_date
2. support search by title/author
3. support checkout with borrower and configurable loan window
4. support return command
5. support overdue listing relative to a supplied or current date
6. expand tests and README accordingly

## Why this slice
This keeps the project simple enough for a student portfolio while showing:
- schema migration thinking
- state transitions
- date handling
- SQL filtering/query design
- better CLI ergonomics
