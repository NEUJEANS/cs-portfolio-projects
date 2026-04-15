# Markdown Notes Search Review Pass 2 — 2026-04-15

## Focus
Ranking and snippet quality.

## Issue found
Best-section selection initially preferred the top-level heading because parent content accidentally inherited subsection text.

## Fix
After correcting section scoping, section-match selection now points to the concrete subsection anchor for body hits like `phi accrual`.
