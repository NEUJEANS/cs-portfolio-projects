# cuckoo-hashing-lab

A portfolio-friendly Python project that implements a cuckoo hash table with deterministic snapshots, CLI workflows, collision-focused tests, and benchmark exports.

## Why it is interesting
- demonstrates an interview-friendly collision resolution strategy with worst-case O(1) lookups
- shows how insertion cycles trigger displacement chains and rehashing
- stays practical by supporting file-based builds, saved snapshots, lookups, removals, exports, and benchmark summaries
- gives you a concrete systems/data-structure project to discuss load factor tradeoffs and rehash behavior

## Features
- dual-hash cuckoo placement with bounded displacement attempts
- automatic rehashing when insertion cycles appear
- snapshot save/load support for resumable demos
- CLI commands for build, stats, lookup, remove, export, and benchmark
- benchmark mode with repeated trials and optional CSV export
- deterministic unit tests that exercise rehashing, invalid snapshot handling, and benchmark flows

## Usage

Build a table snapshot from newline-delimited `key,value` or `key=value` pairs:

```bash
python3 cuckoo_hashing_lab.py build \
  --input sample_keys.txt \
  --output artifacts/cuckoo-table.json \
  --capacity 11 \
  --max-displacements 16
```

Inspect table statistics and current contents:

```bash
python3 cuckoo_hashing_lab.py stats --snapshot artifacts/cuckoo-table.json
```

Lookup a key:

```bash
python3 cuckoo_hashing_lab.py lookup --snapshot artifacts/cuckoo-table.json user:1003
```

Remove a key and write an updated snapshot:

```bash
python3 cuckoo_hashing_lab.py remove \
  --snapshot artifacts/cuckoo-table.json \
  --output artifacts/cuckoo-table-updated.json \
  user:1002
```

Export sorted contents for inspection:

```bash
python3 cuckoo_hashing_lab.py export \
  --snapshot artifacts/cuckoo-table-updated.json \
  --output artifacts/cuckoo-table.csv
```

Benchmark how displacement and rehash counts change across target load factors:

```bash
python3 cuckoo_hashing_lab.py benchmark \
  --capacity 101 \
  --max-displacements 16 \
  --load-factors 0.25,0.4,0.55,0.7,0.8 \
  --trials 5 \
  --output artifacts/cuckoo-benchmark.csv
```

## Test

```bash
python3 -m unittest projects/cuckoo-hashing-lab/test_cuckoo_hashing_lab.py
```

## Future improvements
- add bucketized cuckoo hashing to compare single-slot vs multi-slot bucket behavior
- compare benchmark output against linear probing or separate chaining baselines
- support binary snapshots to compare serialization overhead with plain JSON
