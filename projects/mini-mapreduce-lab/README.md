# mini-mapreduce-lab

A compact Python project that demonstrates the map → combine → reduce pipeline on local text and JSONL data.

## Why it is interesting
- shows the core execution model behind Hadoop-style batch processing without heavy infrastructure
- demonstrates shard partitioning, local combiners, and deterministic reduction
- stays practical with built-in jobs you can run on portfolio-friendly sample datasets

## Features
- line-sharded execution over one or more input files
- built-in `wordcount` job for text analytics
- built-in `json-group-count` job for JSONL event aggregation
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

Write the result to disk:

```bash
python3 projects/mini-mapreduce-lab/mapreduce.py run \
  wordcount sample.txt \
  --output result.json
```

## Test

```bash
python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py
```

## Future improvements
- add a partitioner abstraction to route keys to reducer buckets explicitly
- support external mapper/reducer plugins for custom portfolio demos
- add timing/throughput benchmarks for larger synthetic datasets
