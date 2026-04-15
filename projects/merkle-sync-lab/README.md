# merkle-sync-lab

A portfolio-ready systems project that builds Merkle-tree-style manifests for directories, explains what changed, produces a sync plan to reconcile two snapshots, executes that plan, and now demonstrates chunk-level proofs for partial file sync.

## Why it is portfolio-worthy
- demonstrates hierarchical hashing, a core idea behind Git, content-addressed storage, distributed sync systems, and integrity verification
- turns a theoretical data structure into a practical file integrity and directory comparison tool
- exposes human-readable CLI output plus JSON output for automation and scripting
- includes both directory-level sync planning and file-level chunk proofs, which makes the project feel closer to real replication tooling
- keeps the implementation dependency-free so interviewers can run it instantly

## Features
- recursively hash files with SHA-256 while ignoring common cache metadata directories
- build deterministic directory manifests with child digests rolled up into parent digests
- diff two live directories, two manifests, or a manifest against a directory
- report added, removed, and changed files plus changed directory subtrees
- generate an ordered sync plan with `mkdir`, `copy`, `update`, and `delete` operations
- preview or execute the generated sync plan with dry-run-safe output
- export manifest, diff, plan, and apply JSON for reproducible demos and follow-on tooling
- build chunk-level file Merkle proofs and compare two files chunk-by-chunk
- verify a saved chunk proof artifact against a source root digest

## Usage
Build a manifest:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py build projects/merkle-sync-lab --output /tmp/merkle-manifest.json
```

Compare two directories:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py diff dir_a dir_b
```

Compare a saved manifest against a fresh directory:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py diff /tmp/merkle-manifest.json dir_b --json
```

Generate a sync plan to make `target_dir` match `source_dir`:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py plan source_dir target_dir
```

Generate a machine-readable plan from a saved manifest:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py plan /tmp/merkle-manifest.json target_dir --json
```

Preview the changes that would be applied:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py apply source_dir target_dir
```

Execute the sync plan against a live target directory:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py apply source_dir target_dir --execute
```

Compare two file versions at chunk granularity and emit proofs for changed source chunks:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py chunk-diff old.bin new.bin --chunk-size 4096 --json
```

Verify one changed chunk from saved proof JSON:
```bash
python3 projects/merkle-sync-lab/merkle_sync_lab.py verify-chunk /tmp/chunk-diff.json 3
```

## Example chunk-diff output
```json
{
  "chunk_size": 4,
  "changed_chunk_count": 1,
  "changed_chunks": [
    {
      "index": 1,
      "offset": 4,
      "source_sha256": "2481a63c85a62cf889d2b149f1a52e985a9341750173fe01eff50cc27b5941b5",
      "target_sha256": "e8db10a741d31d2deb85370cd966c807fcc1615ed5b600b987a1a04bbcd3ca1e",
      "source_size": 4,
      "target_size": 4,
      "source_proof": [
        {"position": "right", "digest": "e8db10a741d3..."},
        {"position": "left", "digest": "6aa79987d2d6..."}
      ]
    }
  ],
  "is_identical": false
}
```

## Example plan output
```text
source: /tmp/source
target: /tmp/target
operations: mkdir=1 copy=2 update=1 delete=1
bytes scheduled: copy=84 update=31
  - mkdir docs
  - copy docs/guide.txt (size=42, sha256=0f8c1b6a3d7e)
  - copy docs/index.txt (size=42, sha256=442af8d50f31)
  - update config.json (size=31, sha256=87b442bcf1e4, prev=8a6f425d2b90)
  - delete stale.log (size=128, sha256=1d2fe4cf9a1a)
```

## Example apply output
```text
mode: execute
source: /tmp/source
target: /tmp/target
operations: mkdir=1 copy=2 update=1 delete=1
bytes scheduled: copy=84 update=31
applied operations: 5
  - applied: mkdir docs
  - applied: copy docs/guide.txt
  - applied: copy docs/index.txt
  - applied: update config.json
  - applied: delete stale.log
```

## Test
```bash
python3 -m unittest projects/merkle-sync-lab/test_merkle_sync_lab.py
```

## Future improvements
- add direct partial-sync application so changed chunks can be patched without copying an entire file
- optionally emit Graphviz views of changed directory subtrees or file chunk trees
- add conflict-aware safety policies such as refusing to overwrite locally modified targets without a force flag
