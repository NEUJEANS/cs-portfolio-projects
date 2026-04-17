# Markdown Notes Search Grouped TUI Cluster Slice Checklist

Date: 2026-04-17
Project: `markdown-notes-search`

## Goal
Keep section-result TUI browsing readable when one large note emits many matching anchors by adding a grouped note-level view that still preserves bulk open/export actions.

## Checklist
- [x] confirm this is the next unfinished/weakest markdown-notes-search follow-up item
- [x] skip external web research because the local checklist, README, and prior wrap-up already scoped the slice clearly
- [x] do a short Python/TUI state refresh and local self-test for grouped selection behavior
- [x] update the main project checklist and README before/alongside code changes
- [x] implement grouped TUI rows for dense multi-section note clusters
- [x] keep mark/open/export flows compatible by expanding grouped rows back into their underlying section hits
- [x] add automated tests for grouped TUI helper behavior and selection expansion
- [x] run the project test suite
- [x] perform review pass 1 and fix findings
- [x] perform review pass 2 and fix findings
- [x] perform review pass 3 and fix findings
- [x] run a secret scan before push
- [x] commit, push, and add wrap-up

## Notes
- Grouping should only collapse dense multi-section clusters, not every section result blindly.
- Grouped rows should stay safe for follow-up actions by reopening/exporting the underlying section-scoped results rather than inventing a new output format.
