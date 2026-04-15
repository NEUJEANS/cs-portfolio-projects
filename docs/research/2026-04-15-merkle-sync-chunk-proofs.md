# Merkle sync chunk-proof slice research

## Goal
Add a portfolio-worthy partial-sync story to `merkle-sync-lab` without turning the project into a full rsync clone.

## Notes
- Merkle trees are a natural fit for partial verification because a leaf hash plus its sibling path can prove membership in a larger root digest.
- For a teaching-friendly CLI, fixed-size chunking is simpler than content-defined chunking and still demonstrates the core idea clearly.
- A practical slice can compare two files chunk-by-chunk, report only changed chunk indexes, and attach source-side proofs so a downstream system could verify those chunks against the source root.
- Verification should stay separate and simple: recompute the parent chain from the chunk hash plus proof path and compare it to the advertised root.

## Decision
Implement:
1. chunk-level Merkle proof generation for a single file
2. `chunk-diff` CLI output that reports changed chunks between source and target files
3. `verify-chunk` CLI command to validate a selected chunk proof from saved JSON

## Defer
- content-defined chunking
- rolling checksums / rsync-style block search
- direct partial patch application
- chunk proofs embedded into directory manifests
