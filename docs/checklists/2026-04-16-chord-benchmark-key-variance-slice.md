# Chord DHT benchmark key variance slice

- Timestamp: 2026-04-16 04:41 UTC
- Project: `chord-dht-lab`
- Goal: extend seeded benchmark sample comparisons with per-key variance summaries so portfolio write-ups can call out the most start-node-sensitive lookups.

## Plan
- [x] verify repo sync state before editing
- [x] inspect existing benchmark-sample comparison helpers and README future-work notes
- [x] skip web research because this slice is a direct reporting extension of the existing benchmark sample tooling
- [x] do a short Python aggregation/reporting self-test
- [x] update README/checklist/learning notes for resumability
- [x] add per-key variance summarization helper and Markdown/CSV renderers
- [x] expose the workflow with a dedicated `benchmark-key-variance-export` CLI command
- [x] add or update automated tests for helper ordering, renderers, and CLI output
- [x] run the focused test suite and a compile check
- [x] run secret scan before push
- [x] commit, push, and write wrap-up
