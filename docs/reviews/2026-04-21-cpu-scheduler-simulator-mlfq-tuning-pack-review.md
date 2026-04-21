# CPU Scheduler Simulator Review Log — 2026-04-21 MLFQ Tuning Pack Slice

## Pass 1 — benchmark HTML audit
- issue found: the benchmark HTML only showed `mlfq pack=portfolio` in run settings, which made the tuning bundle harder to understand without reading Markdown/JSON
- fix: added a dedicated `MLFQ tuning roster` card to the benchmark HTML and regenerated the committed bundle

## Pass 2 — CLI coverage audit
- issue found: the new variant-pack path had explicit benchmark CLI coverage but not a compare CLI regression
- fix: added `test_cli_compare_json_output_for_mlfq_variant_pack` so the parser and compare JSON output stay protected

## Pass 3 — docs consistency audit
- issue found: the README still implied alternate MLFQ presets were future work even after this slice shipped named tuning ladders
- fix: refreshed the README feature list, usage examples, artifact notes, and next-extensions section to match the new shipped flow
