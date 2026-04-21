# Extendible hashing lab benchmark-dashboard research — 2026-04-21

## Goal
Add a compact artifact that makes the existing deterministic benchmark suite easier to browse than raw JSON/Markdown/CSV alone.

## Brief research
- MDN table accessibility guidance: use real table structure with `caption`, `thead`, `tbody`, and header cells so screen readers can associate labels with metrics instead of relying on visual layout alone.
  - Source: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Table_accessibility

## Implementation takeaways
- Keep the dashboard self-contained HTML so it can be checked into `docs/artifacts/` and opened directly from GitHub or a local file browser.
- Reuse the exact benchmark summary object already emitted by the CLI so the visual artifact cannot drift from the JSON/Markdown/CSV exports.
- Prefer a compact scoreboard table plus per-scenario metric cards with simple CSS bars over JS-heavy charting; that keeps the artifact deterministic, portable, and easy to review in diffs.
