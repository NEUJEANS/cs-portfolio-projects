# Review Pass 2 — markdown-notes-search section results

Date: 2026-04-16
Focus: CLI and export smoke review

## Checks
- Ran a plain-text smoke command with `--section-results --show-sections --show-open-command`
- Ran a JSON smoke command with `--section-results --json --editor code`

## Findings
1. The feature worked, but the docs still looked like the tool only exposed one best section per note. The new section-scoped mode needed explicit examples so the workflow was discoverable.

## Fixes applied
- Updated `projects/markdown-notes-search/README.md` overview, feature list, usage examples, editor notes, TUI notes, and future-improvement list to document `--section-results`

## Verification
- Plain-text smoke output showed separate anchored hits for `systems.md#failure-recovery` and `systems.md#failure-detection`
- JSON smoke output showed `scope: section`, `path_display`, `matched_terms`, and line-aware `open_command`
