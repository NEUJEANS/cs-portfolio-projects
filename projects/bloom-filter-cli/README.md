# bloom-filter-cli

A small portfolio project that implements standard and counting Bloom filters with a reusable Python API and CLI.

## Why it is interesting
- Demonstrates a probabilistic data structure rather than standard CRUD logic.
- Shows practical hashing, space-efficiency tradeoffs, false-positive analysis, deletion tradeoffs, and artifact-format choices.
- Produces reusable serialized filter artifacts for later queries, approximate removals, and compact binary export.

## Features
- compute Bloom filter size and hash count from capacity and target error rate
- add newline-delimited items from a file
- query saved filters for possible membership
- inspect estimated false-positive rate and load statistics
- benchmark observed false-positive rate with deterministic generated samples
- save/load standard and counting filter state as JSON for resumable usage
- export standard or counting filters into a compact binary artifact format
- compare JSON vs. binary artifact sizes for standard vs. counting filters
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

Check membership from JSON or binary artifacts:

```bash
python3 bloom_filter.py check --filter sample_filter.json apple banana kiwi
python3 bloom_filter.py check --filter sample_filter.bf apple banana kiwi
```

Export a compact binary artifact:

```bash
python3 bloom_filter.py export-binary \
  --filter sample_counting_filter.json \
  --output sample_counting_filter.bf
```

Inspect a binary artifact:

```bash
python3 bloom_filter.py inspect-binary --filter sample_counting_filter.bf
```

Remove items from a counting filter:

```bash
python3 bloom_filter.py remove --filter sample_counting_filter.json banana kiwi
python3 bloom_filter.py remove --filter sample_counting_filter.bf banana kiwi
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

Compare artifact sizes:

```bash
python3 bloom_filter.py compare-sizes \
  --capacity 1000 \
  --error-rate 0.01 \
  --inserted-count 800 \
  --counter-bits 8
```

Example input file: `sample_items.txt`

## Test

```bash
python3 -m unittest projects/bloom-filter-cli/test_bloom_filter.py
```

## Binary artifact notes
- The binary format stores a short header, compact JSON metadata, and a raw payload.
- Standard filters export the bitset as packed bytes.
- Counting filters export fixed-width counters using `ceil(counter_bits / 8)` bytes per counter.
- For a representative run (`capacity=1000`, `error_rate=0.01`, `inserted_count=800`, `counter_bits=8`):
  - standard JSON: 2546 bytes
  - standard binary: 1322 bytes
  - counting JSON: 67306 bytes
  - counting binary: 9750 bytes
  - counting binary is about 7.38× the size of standard binary because delete support stores counters instead of single bits

## Future improvements
- support direct binary output during build commands
- add bulk remove mode from newline-delimited files
- experiment with bit-packed sub-byte counters for even denser counting-filter artifacts
