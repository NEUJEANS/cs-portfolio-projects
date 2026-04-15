# Chord DHT stabilization comparison slice

- Timestamp: 2026-04-15 13:09 UTC
- Project: `projects/chord-dht-lab`
- Goal: compare `single`, `all`, and seeded `random` finger-repair schedules on the same stabilization scenario so the lab teaches trade-offs instead of only exposing one run at a time.

## Plan
- [x] sync repo before editing
- [x] inspect current stabilization/reporting gaps
- [x] skip web research because the comparison slice is a direct extension of the existing stabilization simulator and CLI
- [x] do a short Python reporting/data-shaping self-check
- [x] update checklist/docs so the slice is resumable
- [x] add a comparison helper that runs multiple stabilization modes on the same scenario
- [x] expose the comparison via a dedicated CLI command and demo payload preview
- [x] update README usage and next-step notes
- [x] add/update tests for comparison summaries and CLI behavior
- [x] run tests
- [x] review pass 1
- [x] review pass 2
- [x] review pass 3
- [x] secret scan
- [x] commit, push, wrap-up

## Notes
- Keep `random` mode reproducible by threading a single explicit seed through the comparison run.
- Summaries should report which mode stabilizes first and which mode makes the most finger-table progress when the round budget is too small.
