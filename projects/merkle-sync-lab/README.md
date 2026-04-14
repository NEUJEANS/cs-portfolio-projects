# merkle-sync-lab

A portfolio-ready systems project that builds Merkle-tree-style manifests for directories and diffs snapshots to explain what changed.

## Why it is portfolio-worthy
- demonstrates hierarchical hashing, a core idea behind Git, content-addressed storage, and distributed sync systems
- turns a theoretical data structure into a practical file integrity and directory comparison tool
- exposes both a human-readable CLI and JSON output for automation
- keeps the implementation dependency-free so interviewers can run it instantly

## Features
- recursively hash files with SHA-256 while ignoring common cache metadata directories
- build deterministic directory manifests with child digests rolled up into parent digests
- diff two live directories, two manifests, or a manifest against a directory
- report added, removed, and changed files plus changed directory subtrees
- export manifest JSON for reproducible demos and follow-on tooling

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

## Test
```bash
python3 -m unittest projects/merkle-sync-lab/test_merkle_sync_lab.py
```

## Future improvements
- support chunk-level Merkle trees for large-file partial sync demos
- emit Graphviz views of changed directory subtrees
- add rsync-style copy planning based on diff output
