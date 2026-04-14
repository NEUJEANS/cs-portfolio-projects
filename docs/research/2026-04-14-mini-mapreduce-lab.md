# 2026-04-14 mini-mapreduce lab notes

## Why this project
Existing projects already cover data structures, storage engines, CLIs, HTTP services, and probabilistic algorithms. A tiny MapReduce lab adds a recognizable distributed-systems concept to the portfolio while staying small enough for a resumable vertical slice.

## Scope for this slice
- local-only execution to keep setup trivial
- one text analytics job and one JSONL aggregation job
- explicit shard/combine/reduce phases in code and docs

## Follow-up ideas
- add partitioner/reducer bucket simulation
- benchmark larger synthetic datasets
- visualize skew across shards
