# mini-mapreduce plugin review pass 3

## Focus
Docs and portfolio clarity.

## Findings
1. The initial README plugin contract omitted the shard-local combiner hook, which made the max-score example look inconsistent with the execution pipeline.
2. The project needed an included example plugin so the extensibility story was runnable, not just documented.

## Fixes applied
- Updated README with the full plugin contract including optional `combine_values`.
- Added `plugins_top_score.py` as a concrete demo plugin and documented a CLI example around it.
