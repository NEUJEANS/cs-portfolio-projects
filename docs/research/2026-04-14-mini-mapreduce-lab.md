# 2026-04-14 mini-mapreduce lab notes

## Why this project
Existing projects already cover data structures, storage engines, CLIs, HTTP services, and probabilistic algorithms. A tiny MapReduce lab adds a recognizable distributed-systems concept to the portfolio while staying small enough for a resumable vertical slice.

## Scope for the initial slice
- local-only execution to keep setup trivial
- one text analytics job and one JSONL aggregation job
- explicit shard/combine/reduce phases in code and docs

## Follow-up slice chosen this run
The most obvious gap was the lack of an explicit partitioner/reducer stage even though the README mentioned MapReduce concepts. A portfolio-ready improvement is to simulate reducer buckets locally, expose deterministic key routing, and report reducer distribution stats so the student can discuss skew and load balance.

## Follow-up ideas
- benchmark larger synthetic datasets
- visualize skew across shards
- support external mapper/reducer plugins
