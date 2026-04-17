# Markdown Notes Search Collapsed Section Bundles Slice Checklist

Date: 2026-04-17
Project: `markdown-notes-search`

## Goal
Keep dense `--section-results` output readable outside the TUI by collapsing multi-section note clusters into one review-friendly plain-text / JSON / export entry.

## Checklist
- [x] confirm this is the next unfinished/weakest markdown-notes-search follow-up item
- [x] skip external web research because the local checklist, README, and prior wrap-up already scoped the slice clearly
- [x] skip extra language refresh because the slice reuses the same section-grouping/data-shaping patterns as the recent TUI grouping work
- [x] update the main project checklist and README before/alongside code changes
- [x] implement `--collapse-sections` for plain-text, JSON, and export flows
- [x] keep grouped output actionable by preserving the strongest section jump target plus the grouped section-hit list
- [x] add automated tests for output-collapsing helpers, collapsed formatting, export bundles, and CLI behavior
- [x] run the project test suite
- [x] perform review pass 1 and fix findings
- [x] perform review pass 2 and fix findings
- [x] perform review pass 3 and fix findings
- [x] run a secret scan before push
- [x] commit, push, and add wrap-up

## Notes
- TUI grouping already exists behind the interactive `g` toggle; this slice should help plain CLI and exported review artifacts catch up.
- Collapsed bundles should not throw away the exact section anchors; they should summarize them while still exposing the top jump target and full grouped list.
