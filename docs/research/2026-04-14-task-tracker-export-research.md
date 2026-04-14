# Task Tracker Export Slice Research

Date: 2026-04-14

## Goal
Add an export feature that makes the task tracker more portfolio-ready by showing interoperability with common formats.

## Brief notes
- CSV export is a strong default because it is easy to inspect, import into spreadsheets, and validate in tests.
- Markdown export is useful for developer-facing status notes, README snippets, and project planning docs.
- A good CLI export slice should support the same filtering options as `list` so users can export focused subsets, not only the full dataset.
- Writing to stdout when no output path is provided keeps the tool composable in shell pipelines, while `--output` supports direct file generation.

## Slice decision
Implement `export` with:
- `--format csv|markdown`
- `--output PATH` optional
- existing list filters: `--status`, `--priority`, `--search`, `--tag`, `--sort-by`
- summary block for Markdown export

## Success bar
- export output is deterministic enough for tests
- generated files are human-readable
- README includes examples for both formats
