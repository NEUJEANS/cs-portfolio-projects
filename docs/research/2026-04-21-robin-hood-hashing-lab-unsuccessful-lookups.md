# Research — robin-hood-hashing-lab unsuccessful lookups — 2026-04-21

## Goal
Make search misses part of the benchmark story instead of only tracking resident probe-distance spread and successful lookups.

## References checked
1. Code Capsule, `Robin Hood hashing` (fetched 2026-04-21)
   - emphasizes the original Robin Hood claim that probe-sequence variance stays small, which supports comparing miss costs and not only average successful lookups.
   - also highlights the distinction between bucket distance and the number of inspected entries, which matters when reporting failed-search probe counts separately from resident probe distances.
2. thenumb.at, `Optimizing Open Addressing` (fetched 2026-04-21)
   - compares open-addressing strategies in terms of practical lookup behavior and reinforces that missing-key performance is an important real-world metric, especially as clustering grows.

## Design takeaways
- Keep the existing fill-only and delete-heavy workloads.
  - They already create the table states worth comparing.
  - The missing-key story can be measured after each workload instead of adding a redundant third workload.
- Add a dedicated unsuccessful-lookup histogram rather than overloading the resident probe-distance histogram.
  - Resident probe distance explains where entries sit.
  - Failed-search probes explain how many slots a search must inspect when the key is absent.
- Reuse deterministic seeds for the missing-key probes.
  - That keeps the benchmark outputs reproducible for committed artifact regeneration.
- Surface miss metrics in Markdown, HTML, CSV, and JSON together.
  - The portfolio story is strongest when the benchmark bundle stays internally consistent across all export formats.
