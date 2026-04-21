# robin-hood-hashing-lab key profile review log

Date: 2026-04-21

## Review pass 1, report tables dropped the new dimension
- The first draft threaded `key_profile` through the raw summary data, but several Markdown/HTML tables and histogram lookups still keyed rows only by workload/load factor/strategy.
- Problem found: multi-profile runs would merge or hide slices in the rendered report even though the benchmark rows were present.
- Fix: updated summary lookup keys, comparison tables, percentile tables, aggregate tables, and histogram sections so they all group by key profile as well.

## Review pass 2, integer miss-key generation could underfill
- The first integer missing-key generator created a fixed shuffled list and filtered collisions only after generation.
- Problem found: if a generated decimal ID overlapped an existing integer-profile key, the filtered result could end up shorter than the requested count.
- Fix: switched to a deterministic generate-until-full loop before shuffling, so the integer miss-key set always stays disjoint and reaches the requested size.

## Review pass 3, regression coverage initially missed the CLI/report surface area
- The first test pass covered parser and generator helpers, but not the user-visible benchmark outputs.
- Problem found: it was too easy for `--key-profiles` or report rendering changes to regress while unit helpers still passed.
- Fix: extended the CLI benchmark flow test, added multi-profile Markdown/HTML assertions, and verified CSV/JSON rows now emit the `key_profile` field.
