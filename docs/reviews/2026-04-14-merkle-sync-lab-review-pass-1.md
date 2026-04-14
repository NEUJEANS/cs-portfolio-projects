# Review Pass 1 - merkle-sync-lab

## Focus
Core correctness and deterministic hashing.

## Findings
- File and directory ordering must be sorted so digest output is stable.
- Directory digest input should include both path labels and child digests.

## Fixes applied
- kept traversal sorted
- encoded child entries with `file:` / `dir:` prefixes and paths before hashing
