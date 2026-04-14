# mini-mapreduce-lab

A compact Python project that demonstrates the map → combine → partition → reduce pipeline on local text and JSONL data.

## Why it is interesting
- shows the core execution model behind Hadoop-style batch processing without heavy infrastructure
- demonstrates shard partitioning, local combiners, deterministic reducer routing, and deterministic reduction
- stays practical with built-in jobs you can run on portfolio-friendly sample datasets

## Features
- line-sharded execution over one or more input files
- built-in `wordcount` job for text analytics
- built-in `json-group-count` job for JSONL event aggregation
- stable SHA-256-based partitioner to simulate multiple reducer buckets reproducibly across processes
- reducer distribution stats so you can talk about key skew in interviews
- synthetic `benchmark` mode for balanced vs skewed workloads across multiple reducer counts
- machine-readable JSON output with shard and record statistics

## Usage

Word count over text files:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample_a.txt sample_b.txt \
  --shard-size 50
```

Count JSONL records by a field:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  json-group-count events.jsonl \
  --group-field status \
  --shard-size 100
```

Simulate multiple reducers and inspect skew:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample.txt \
  --shard-size 50 \
  --reducers 4
```

Benchmark balanced vs skewed synthetic inputs:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario skewed \
  --records 5000 \
  --shard-size 250 \
  --reducers 1 2 4 8
```

Write the benchmark result to disk:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py benchmark \
  --scenario balanced \
  --reducers 1 4 8 \
  --output benchmark.json
```

## Output shape

```json
{
  "reducers": [1, 2, 4],
  "scenario": "skewed",
  "seed": 42,
  "shard_size": 250,
  "timings_ms": [
    {
      "elapsed_ms": 4.112,
      "map_records": 10000,
      "max_reducer_records": 8123,
      "reducers": 4,
      "shards": 20,
      "skew_ratio": 3.249,
      "unique_keys": 25
    }
  ],
  "total_records": 5000,
  "unique_keys": 25
}
```

## Test

```bash
python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py
```

## Interview talking points
- why combiners reduce shuffle volume before the global reduce step
- how partitioning affects reducer balance and hot-key skew
- how deterministic benchmark fixtures make systems demos reproducible
- why timing alone can mislead without reducer-distribution metrics beside it

## Future improvements
- support external mapper/reducer plugins for custom portfolio demos
- export benchmark runs as CSV for charting in notebooks or slide decks
- visualize reducer skew across shards over time
