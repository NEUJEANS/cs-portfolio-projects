# Chord DHT churn workload comparison slice

- Timestamp: 2026-04-16 04:01 UTC
- Project: `projects/chord-dht-lab`
- Goal: compare multiple churn workload files side by side so the lab can explain workload sensitivity instead of showcasing only one event sequence.

## Plan
- [x] sync repo before editing
- [x] inspect current churn tooling and pick the weakest unfinished reporting gap
- [x] skip web research because workload comparison is a direct extension of the existing churn report/export pipeline
- [x] do a short Python/report-shaping self-check
- [x] update/add checklist markdown so the slice is resumable
- [x] implement multi-workload churn comparison helpers plus Markdown/CSV export
- [x] expose the comparison via a dedicated CLI command
- [x] update README usage and future-improvements notes
- [x] extend automated coverage for helpers and CLI behavior
- [x] run tests
- [x] review pass 1
- [x] review pass 2
- [x] review pass 3
- [x] secret scan
- [ ] commit, push, wrap-up

## Notes
- Keep comparison deterministic by reusing the existing `churn_report` result for each workload file.
- Include both a scoreboard and per-step snapshots so the output helps both README snippets and spreadsheet/chart workflows.
