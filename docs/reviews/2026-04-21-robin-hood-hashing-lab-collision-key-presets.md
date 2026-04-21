# robin-hood-hashing-lab collision key preset review log

Date: 2026-04-21

## Review pass 1, reports initially hid the new benchmark dimension
- The first draft threaded `key_preset` through raw benchmark rows, but the rendered tables and histogram lookup keys were still effectively profile/workload/load-factor centric.
- Problem found: multi-preset runs were too easy to misread because rows could not clearly distinguish `uniform` from `collision-focused` slices.
- Fix: updated summary grouping/lookup keys to include `key_preset`, added preset metadata to rows/comparisons, and rendered combined `key profile / preset` labels throughout Markdown and HTML.

## Review pass 2, PNG sizing underestimated dense multi-preset dashboards
- The original PNG-height heuristic only scaled with key profiles and workloads.
- Problem found: once `collision-focused` slices were added, dense dashboard captures risked being cropped because the extra histogram sections were not counted.
- Fix: updated `default_benchmark_png_height()` so it scales with key presets too.

## Review pass 3, hotspot pressure needed to cover misses as well as resident keys
- The first collision-focused generator only mattered for inserted keys.
- Problem found: unsuccessful lookups could still use uniformly spread missing keys, which would blunt the clustering story in the miss histograms.
- Fix: extended missing-key generation to honor the same `collision-focused` preset and added regression coverage to prove the hotspot-targeted generator stays deterministic and disjoint from resident keys.
