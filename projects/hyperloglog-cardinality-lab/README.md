# hyperloglog-cardinality-lab

A portfolio-friendly Python project that implements a HyperLogLog sketch for approximate distinct counting.

## Why it is interesting
- demonstrates a classic probabilistic data structure used in analytics systems
- shows the tradeoff between memory usage and estimation accuracy
- includes sketch merge support, which maps well to distributed systems conversations
- stays practical: you can build sketches from files and inspect accuracy with simulations

## Features
- configurable precision (`2^p` registers)
- newline-delimited file ingestion into a reusable JSON sketch
- distinct-count estimation with small-range correction
- sketch merge support for combining partial counts
- simulation mode to compare observed error with the theoretical error bound

## Usage

Build a sketch from newline-delimited input:

```bash
python3 hyperloglog.py build \
  --input sample_users.txt \
  --output users_hll.json \
  --precision 10
```

Inspect sketch statistics:

```bash
python3 hyperloglog.py stats --sketch users_hll.json
```

Merge sketches from multiple shards (with the same precision):

```bash
python3 hyperloglog.py merge \
  --output merged_hll.json \
  shard_a.json shard_b.json shard_c.json
```

Sample estimation accuracy:

```bash
python3 hyperloglog.py simulate \
  --precision 10 \
  --cardinality 5000 \
  --trials 20 \
  --seed 42
```

## Test

```bash
python3 -m unittest projects/hyperloglog-cardinality-lab/test_hyperloglog.py
```

## Future improvements
- add register compression to compare dense vs sparse storage
- support CSV/JSON field extraction instead of only newline-delimited input
- add side-by-side Bloom filter and HyperLogLog demos for probabilistic data structure interviews
