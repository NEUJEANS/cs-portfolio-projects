# robin-hood-hashing-lab

A portfolio-friendly Python project that implements a Robin Hood hash table with backward-shift deletion, deterministic snapshots, a benchmark CLI, and fill-only plus delete-heavy benchmark artifacts that now surface both resident probe-distance spread and unsuccessful-lookup cost across uniform and collision-focused workloads.

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
- benchmark mode for comparing Robin Hood hashing against a linear-probing baseline across load factors, workload shapes, and key presets
- benchmark key profiles for random string IDs and shuffled sequential integer IDs, so the same workload suite can be replayed across multiple input shapes without changing the string-key snapshot format
- benchmark key presets for both uniform spread and collision-focused hotspots, so the same identifier shapes can be replayed under intentionally clustered home-slot pressure
- optional fill-only and delete-heavy workloads so post-removal clustering/backward-shift behavior is visible in the exported metrics
- benchmark output now includes unsuccessful-lookup probe metrics plus failed-search histograms, so misses are part of the same interview story as successful lookups and resident probe distances
- benchmark reports now surface side-by-side successful vs unsuccessful lookup avg/p50/p95/max callouts, so hit and miss tails are readable without scanning every histogram row
- optional Markdown, self-contained HTML, and slide-ready PNG benchmark artifacts with probe-distance histograms plus lookup percentile callouts for portfolio-ready writeups
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

Benchmark Robin Hood hashing against a linear-probing baseline and emit screenshot-friendly artifacts, including string and integer key profiles, uniform plus collision-focused key presets, both fill-only and delete-heavy workload passes, resident probe-distance histograms, and side-by-side hit/miss lookup percentile callouts in the Markdown/HTML reports:

```bash
python3 robin_hood_hashing_lab.py benchmark \
  --capacity 127 \
  --load-factors 0.25,0.5,0.7,0.85 \
  --trials 5 \
  --seed 17 \
  --key-profiles string,integer \
  --key-presets uniform,collision-focused \
  --strategies robin-hood,linear-probing \
  --workloads fill-only,delete-heavy \
  --delete-fraction 0.3 \
  --markdown-out artifacts/robin-hood-benchmark-report.md \
  --html-out artifacts/robin-hood-benchmark-dashboard.html \
  --png-out artifacts/robin-hood-benchmark-dashboard.png \
  --output artifacts/robin-hood-benchmark.json
```

Requested load factors are rounded to whole entry counts for the chosen capacity, so the reports show both the requested target and the effective post-workload load factor.

`--key-profiles` accepts `string` and `integer`. The integer profile uses shuffled sequential decimal IDs so the benchmark can compare compact numeric identifiers against longer text-like IDs while keeping the hash-table implementation itself string-keyed.

`--key-presets` accepts `uniform` and `collision-focused`. The collision-focused preset deterministically filters generated keys down to a small hotspot set of home slots, so both successful and unsuccessful lookups can be replayed under intentionally clustered pressure instead of only naturally spread hashes.

`--png-out` captures a Chrome/Chromium headless screenshot from a compact screenshot mode of the generated HTML dashboard, hiding lower-priority sections so the exported image stays slide-friendly. Pair it with `--html-out` and optionally pass `--chrome-binary` when the browser is not already on `PATH`.

## Sample committed artifacts
- `docs/artifacts/robin-hood-hashing-lab/sample-table.json`
- `docs/artifacts/robin-hood-hashing-lab/sample-table.csv`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html`
- `docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.png`

## Test

```bash
python3 -m unittest tests.test_robin_hood_hashing_lab -v
```

## Future improvements
- add a compact benchmark takeaway card that highlights where Robin Hood wins or loses most under each key preset
