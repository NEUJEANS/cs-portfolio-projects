# robin-hood-hashing-lab unsuccessful lookups review log

Date: 2026-04-21

## Review pass 1, metric separation
- Re-read the first implementation to confirm the new miss metric was not being conflated with resident probe distance.
- Kept a dedicated unsuccessful-lookup histogram and average miss-probe field in the benchmark rows, summary, CSV, JSON, Markdown, and HTML outputs.

## Review pass 2, comparison wording clarity
- The headline table originally used generic `Lookup winner` wording even though the slice now reports both hit and miss behavior.
- Fix: split the comparison language into successful lookup and unsuccessful lookup winners/deltas so the report reads cleanly in screenshots.

## Review pass 3, pooled-count wording bug
- The first draft of the unsuccessful-lookup histogram narrative reported the pooled trial total as if it were a per-trial sample count.
- Fix: divide the aggregated histogram count by the deterministic trial count before rendering the `per trial` sentence in Markdown and HTML.
