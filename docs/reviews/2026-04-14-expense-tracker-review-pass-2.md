# Expense Tracker Review Pass 2 — 2026-04-14

## Focus
Filter UX and data access behavior.

## Issue found
Category filtering was case-sensitive, so `FOOD` and `food` behaved differently in list views.

## Fix
- changed category filtering to use `COLLATE NOCASE`
- expanded tests to cover mixed-case stored categories and uppercase filter input
