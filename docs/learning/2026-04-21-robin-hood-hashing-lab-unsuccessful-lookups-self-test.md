# robin-hood-hashing-lab unsuccessful lookups self-test

Date: 2026-04-21

## Quick refresh
- Resident probe distance and failed-search probe counts are related, but they are not the same metric.
- If a summary merges histograms across trials, any human-facing `per trial` note must divide back by the number of deterministic trials instead of printing the pooled total.
- Deterministic benchmark extras should reuse seeded generation so committed CSV/JSON/Markdown/HTML artifacts stay stable across reruns.

## Self-test
1. Why add a second histogram instead of reusing the resident probe-distance histogram?
   - Because resident probe distance describes the entries already in the table, while unsuccessful lookup probes describe how far a search walks before it can prove the key is absent.
2. Why avoid adding a brand-new benchmark workload just for misses?
   - Because fill-only and delete-heavy already create the table states that matter. Measuring misses after those states keeps the benchmark easier to explain and avoids redundant artifact rows.
3. What is the easy reporting bug when merging trial histograms?
   - Accidentally calling an aggregated total a `per trial` count. The text has to divide by the trial count when that wording is used.
