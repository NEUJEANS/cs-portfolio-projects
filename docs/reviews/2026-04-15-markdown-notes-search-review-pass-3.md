# Markdown Notes Search Review Pass 3 — 2026-04-15

## Focus
Regression safety and CLI output compatibility.

## Issue found
Exact heading-hit snippets regressed from `Heading: ...` to `Section: ...`, which would break established expectations and tests.

## Fix
Restored heading-first snippets for direct heading matches while still emitting structured `section_match` metadata and optional `--show-sections` plain-text output.
