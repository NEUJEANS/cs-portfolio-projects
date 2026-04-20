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
- CLI commands for workload execution, snapshot inspection, lookups, and deletions
- unit tests that cover bucket splits, merges, directory shrinking, snapshot validation, and CLI flows

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

## Test

```bash
python3 -m unittest tests.test_extendible_hashing_lab -v
```

## Future improvements
- benchmark extendible hashing against linear probing, cuckoo hashing, or B-tree pages under mixed workloads
- export SVG or HTML visualizations that animate aliasing directory entries during repeated splits and merges
