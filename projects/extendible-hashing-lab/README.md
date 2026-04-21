# extendible-hashing-lab

A portfolio-friendly Python lab that implements an extendible hash index with dynamic bucket splitting/merging, persisted snapshots, workload traces, and deterministic tests.

## Why it is interesting
- demonstrates a classic database indexing technique that grows one bucket at a time instead of rehashing the full table
- gives you a concrete way to explain global depth, local depth, aliasing directory entries, and split behavior in interviews
- stays practical with JSON workload inputs, snapshot persistence, inspection commands, and Markdown trace exports
- complements the repo's B-tree, LSM-tree, and cuckoo-hashing projects with a dynamic hash directory design

## Features
- deterministic 64-bit FNV-1a hashing for reproducible demos and tests
- extendible directory growth with per-bucket local depth tracking
- bucket merge and directory shrink support so delete-heavy runs can demonstrate the full lifecycle
- JSON snapshot save/load support for resumable inspection workflows
- workload runner that records per-step growth and can export a Markdown trace report
- self-contained SVG/HTML visualization exports that show split sequences, directory aliasing, and bucket-local-depth changes per step while preserving full details through hover/tooltips
- benchmark mode that compares extendible hashing against the repo's cuckoo-hashing and B-tree labs across JSON suite scenarios with JSON/Markdown/CSV outputs
- CLI commands for workload execution, snapshot inspection, lookups, deletions, visualization exports, and benchmark exports
- unit tests that cover bucket splits, merges, directory shrinking, visualization rendering, benchmark validation, and CLI flows

## Usage

Run the sample workload and save both a snapshot and a Markdown report:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py run \
  --input projects/extendible-hashing-lab/sample_workload.json \
  --output /tmp/extendible-snapshot.json \
  --report /tmp/extendible-report.md
```

Inspect the saved snapshot as Markdown:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py inspect \
  --snapshot /tmp/extendible-snapshot.json \
  --format markdown
```

Lookup a key:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py lookup \
  --snapshot /tmp/extendible-snapshot.json \
  user:1009
```

See the committed demo outputs without rerunning anything:
- `docs/artifacts/extendible-hashing-lab/sample_workload_snapshot.json`
- `docs/artifacts/extendible-hashing-lab/sample_workload_report.md`
- `docs/artifacts/extendible-hashing-lab/sample_snapshot_inspect.md`
- `docs/artifacts/extendible-hashing-lab/delete_heavy_workload_snapshot.json`
- `docs/artifacts/extendible-hashing-lab/delete_heavy_workload_report.md`
- `docs/artifacts/extendible-hashing-lab/delete_heavy_snapshot_inspect.md`

Delete a key and persist the updated snapshot:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py delete \
  --snapshot /tmp/extendible-snapshot.json \
  --output /tmp/extendible-snapshot-updated.json \
  user:1017
```

Run the delete-heavy workload that grows to depth 2 and then shrinks back to depth 0:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py run \
  --input projects/extendible-hashing-lab/delete_heavy_workload.json \
  --output /tmp/extendible-delete-heavy.json \
  --report /tmp/extendible-delete-heavy.md
```

Render a split/aliasing visualization for the sample workload:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py visualize \
  --input projects/extendible-hashing-lab/sample_workload.json \
  --svg-out /tmp/extendible-trace.svg \
  --html-out /tmp/extendible-trace.html \
  --title 'Extendible hashing split and aliasing trace'
```

Compare extendible hashing against the repo's cuckoo-hashing and B-tree labs across the committed suite:

```bash
python3 projects/extendible-hashing-lab/extendible_hashing_lab.py benchmark \
  --input projects/extendible-hashing-lab/benchmark_suite.json \
  --json-out /tmp/extendible-benchmark.json \
  --markdown-out /tmp/extendible-benchmark.md \
  --csv-out /tmp/extendible-benchmark.csv \
  --title 'Extendible hashing vs cuckoo hashing and B-tree benchmark comparison'
```

See the committed visualization + benchmark demo outputs without rerunning anything:
- `docs/artifacts/extendible-hashing-lab/sample_workload_trace.svg`
- `docs/artifacts/extendible-hashing-lab/sample_workload_trace.html`
- `docs/artifacts/extendible-hashing-lab/delete_heavy_workload_trace.svg`
- `docs/artifacts/extendible-hashing-lab/delete_heavy_workload_trace.html`
- `docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.json`
- `docs/artifacts/extendible-hashing-lab/benchmark_suite_report.md`
- `docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.csv`

## Test

```bash
python3 -m unittest tests.test_extendible_hashing_lab -v
```

## Future improvements
- add a linear-probing baseline or small benchmark dashboard so the project can tell an even broader indexing-tradeoff story
- add compact PNG export or thumbnail-strip generation for the visualization dashboard so README screenshots stay easy to embed
