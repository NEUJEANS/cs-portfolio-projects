# bloom-filter-cli

A small portfolio project that implements a Bloom filter with a reusable Python API and CLI.

## Why it is interesting
- Demonstrates a probabilistic data structure rather than standard CRUD logic.
- Shows practical hashing, space-efficiency tradeoffs, and false-positive analysis.
- Produces a reusable serialized filter artifact for later queries.

## Features
- compute Bloom filter size and hash count from capacity and target error rate
- add newline-delimited items from a file
- query a saved filter for possible membership
- inspect estimated false-positive rate and load statistics
- benchmark observed false-positive rate with deterministic generated samples
- save/load filter state as JSON for resumable usage

## Usage

Build a filter:

```bash
python3 bloom_filter.py build \
  --input sample_items.txt \
  --output sample_filter.json \
  --capacity 1000 \
  --error-rate 0.01
```

Check membership:

```bash
python3 bloom_filter.py check --filter sample_filter.json apple banana kiwi
```

View stats:

```bash
python3 bloom_filter.py stats --filter sample_filter.json
```

Benchmark sampled false positives:

```bash
python3 bloom_filter.py benchmark \
  --capacity 1000 \
  --error-rate 0.01 \
  --inserted-count 800 \
  --probe-count 5000 \
  --seed 42
```

Example input file: `sample_items.txt`

## Test

```bash
python3 -m unittest projects/bloom-filter-cli/test_bloom_filter.py
```

## Future improvements
- add counting Bloom filter support for approximate deletion
- support binary serialization for larger filters
