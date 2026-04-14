# bloom-filter-cli

A small portfolio project that implements standard and counting Bloom filters with a reusable Python API and CLI.

## Why it is interesting
- Demonstrates a probabilistic data structure rather than standard CRUD logic.
- Shows practical hashing, space-efficiency tradeoffs, false-positive analysis, and delete support tradeoffs.
- Produces reusable serialized filter artifacts for later queries and approximate removals.

## Features
- compute Bloom filter size and hash count from capacity and target error rate
- add newline-delimited items from a file
- query a saved filter for possible membership
- inspect estimated false-positive rate and load statistics
- benchmark observed false-positive rate with deterministic generated samples
- save/load standard and counting filter state as JSON for resumable usage
- build a counting Bloom filter variant with delete support and overflow checks

## Usage

Build a standard filter:

```bash
python3 bloom_filter.py build \
  --input sample_items.txt \
  --output sample_filter.json \
  --capacity 1000 \
  --error-rate 0.01
```

Build a counting filter:

```bash
python3 bloom_filter.py build-counting \
  --input sample_items.txt \
  --output sample_counting_filter.json \
  --capacity 1000 \
  --error-rate 0.01 \
  --counter-bits 8
```

Check membership:

```bash
python3 bloom_filter.py check --filter sample_filter.json apple banana kiwi
```

Remove items from a counting filter:

```bash
python3 bloom_filter.py remove --filter sample_counting_filter.json banana kiwi
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
- support binary serialization for larger filters
- compare standard vs. counting memory overhead in a benchmark note
