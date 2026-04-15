# Markdown Notes Search Review Pass 1 — 2026-04-15

## Focus
Section extraction correctness.

## Issue found
Initial section parsing leaked subsection body text into the parent section content.

## Fix
Changed section parsing so only the currently active heading collects body lines, while duplicate headings still receive unique anchors.
