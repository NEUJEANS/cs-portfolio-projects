# robin-hood-hashing-lab

A portfolio-friendly Python project that implements a Robin Hood hash table with backward-shift deletion, deterministic snapshots, a benchmark CLI, and tests that make the probe-distance story easy to explain in interviews.

## Why it is interesting
- demonstrates a classic open-addressing strategy that reduces probe-length variance by letting "poorer" keys steal slots from "richer" ones
- shows how backward-shift deletion preserves lookup guarantees without tombstone buildup
- turns a theory-heavy hashing topic into a practical CLI and benchmark project you can run locally
- gives you a concrete artifact for discussing load factor, clustering, swaps, and predictable lookup behavior

## Features
- Robin Hood insertion with swap counting and deterministic SHA-256-based hashing
- backward-shift deletion instead of tombstones
- JSON snapshot save/load for resumable demos
- CLI commands for build, stats, lookup, remove, export, and benchmark
- benchmark mode for comparing Robin Hood hashing against a linear-probing baseline across load factors
- optional Markdown and self-contained HTML benchmark artifacts with probe-distance histograms for portfolio-ready writeups
- committed sample artifacts under `docs/artifacts/robin-hood-hashing-lab/`
- regression tests covering swaps, deletions, snapshots, CLI flows, and comparison/report generation

## Usage

Build a snapshot from newline-delimited `key,value` or `key=value` pairs. The build flow automatically resizes if the requested capacity would exceed the configured max load factor:

```bash
python3 robin_hood_hashing_lab.py build \
  --input sample_pairs.txt \
  --output artifacts/robin-hood-table.json \
  --capacity 11 \
  --pretty
```

Inspect table statistics:

```bash
python3 robin_hood_hashing_lab.py stats \
  --snapshot artifacts/robin-hood-table.json \
  --pretty
```

Lookup a key:

```bash
python3 robin_hood_hashing_lab.py lookup \
  --snapshot artifacts/robin-hood-table.json \
  user:1003
```

Remove a key and save an updated snapshot:

```bash
python3 robin_hood_hashing_lab.py remove \
  --snapshot artifacts/robin-hood-table.json \
  --output artifacts/robin-hood-table-updated.json \
  user:1002
```

Export sorted entries to CSV:

```bash
python3 robin_hood_hashing_lab.py export \
  --snapshot artifacts/robin-hood-table-updated.json \
  --output artifacts/robin-hood-table.csv
```

Benchmark Robin Hood hashing against a linear-probing baseline and emit screenshot-friendly artifacts, including probe-distance histograms in the Markdown/HTML reports:

```bash
python3 robin_hood_hashing_lab.py benchmark \
  --capacity 127 \
  --load-factors 0.25,0.5,0.7,0.85 \
  --trials 5 \
  --seed 17 \
  --strategies robin-hood,linear-probing \
  --markdown-out artifacts/robin-hood-benchmark-report.md \
  --html-out artifacts/robin-hood-benchmark-dashboard.html \
  --output artifacts/robin-hood-benchmark.json
```

## Sample committed artifacts
- `docs/artifacts/robin-hood-hashing-lab/sample-table.json`
- `docs/artifacts/robin-hood-hashing-lab/sample-table.csv`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html`

## Test

```bash
python3 -m unittest tests.test_robin_hood_hashing_lab -v
```

## Future improvements
- support delete-heavy benchmark workloads now that the compare dashboard and histograms exist
- support unsuccessful-lookup histograms so search misses become part of the interview story too
- support string and integer key generators for more workload shapes
