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

Write the result to disk:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample.txt \
  --reducers 2 \
  --output result.json
```

## Output shape

```json
{
  "job": "wordcount",
  "reducers": 2,
  "reducer_stats": [
    {"reducer": 0, "unique_keys": 1, "records": 1},
    {"reducer": 1, "unique_keys": 1, "records": 2}
  ],
  "output": {
    "alpha": 2,
    "beta": 1
  }
}
```

## Test

```bash
python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py
```

## Interview talking points
- why combiners reduce shuffle volume before the global reduce step
- how partitioning affects reducer balance and hot-key skew
- why deterministic hashing and sorted output make demos and tests reproducible

## Future improvements
- support external mapper/reducer plugins for custom portfolio demos
- add timing/throughput benchmarks for larger synthetic datasets
- visualize reducer skew across shards over time
