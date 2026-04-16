# Chord DHT benchmark export slice

- Timestamp: 2026-04-16 02:01 UTC
- Project: `projects/chord-dht-lab`
- Goal: turn raw lookup benchmark JSON into portfolio-ready Markdown/CSV exports so the project is easier to showcase and compare.

## Plan
- [x] sync repo before editing
- [x] inspect current benchmark/reporting gaps and choose the weakest missing portfolio artifact
- [x] skip web research because benchmark export is a direct extension of the existing benchmark payload and project roadmap
- [x] do a short Python/report-shaping self-check
- [x] update/add checklist markdown so the slice is resumable
- [x] implement benchmark export helpers for Markdown and CSV
- [x] expose the export via a dedicated CLI command
- [x] update README usage and future-improvements notes
- [x] run tests
- [x] review pass 1
- [x] review pass 2
- [x] review pass 3
- [ ] secret scan
- [ ] commit, push, wrap-up

## Notes
- Keep the export deterministic by reusing the existing benchmark payload instead of rebuilding benchmark logic in parallel.
- Include both case-level rows and top-level summary bullets so the output works for both quick README snippets and spreadsheet/chart pipelines.
