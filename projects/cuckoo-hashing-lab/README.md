# cuckoo-hashing-lab

A portfolio-friendly Python project that implements a cuckoo hash table with deterministic snapshots, CLI workflows, and collision-focused tests.

## Why it is interesting
- demonstrates an interview-friendly collision resolution strategy with worst-case O(1) lookups
- shows how insertion cycles trigger displacement chains and rehashing
- stays practical by supporting file-based builds, saved snapshots, lookups, removals, and exports
- gives you a concrete systems/data-structure project to discuss load factor tradeoffs and rehash behavior

## Features
- dual-hash cuckoo placement with bounded displacement attempts
- automatic rehashing when insertion cycles appear
- snapshot save/load support for resumable demos
- CLI commands for build, stats, lookup, remove, and export
- deterministic unit tests that exercise rehashing and invalid snapshot handling

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

## Test

```bash
python3 -m unittest projects/cuckoo-hashing-lab/test_cuckoo_hashing_lab.py
```

## Future improvements
- add bucketized cuckoo hashing to compare single-slot vs multi-slot bucket behavior
- add a benchmark mode that plots load factor against displacement and rehash counts
- support binary snapshots to compare serialization overhead with plain JSON
