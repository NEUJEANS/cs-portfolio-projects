# Learning/self-test — library-manager-sqlite dashboard export slice — 2026-04-21

## Refresh target
Small Python patterns for static report generation from SQLite-backed state.

## Quick refresh
- keep export generation pure: build one snapshot dictionary first, then render Markdown/HTML from that shared structure
- prefer standard-library helpers (`html.escape`, `pathlib.Path`, `datetime`) over extra dependencies for a compact CLI portfolio project
- normalize export timestamps so repeat renders are reproducible when needed
- treat a chosen reference date as an "as-of" boundary, not just a label, or historical snapshots become misleading

## Self-test
Before coding, sanity-checked the slice with four quick questions:
- can the same snapshot drive both terminal-friendly Markdown and screenshot-friendly HTML?
- if a loan is returned after the requested snapshot date, should it still count as active in that earlier snapshot? (yes)
- can I regenerate a committed sample artifact byte-for-byte with a fixed timestamp? (should be yes)
- are captions, header scopes, and timestamp markup enough to make the HTML artifact understandable without JS? (yes)

## Outcome
Safe to implement the dashboard as a standard-library-only export feature instead of adding templates, frameworks, or a live preview server.
