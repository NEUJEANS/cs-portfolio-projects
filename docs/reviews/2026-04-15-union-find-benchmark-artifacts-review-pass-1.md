# Review pass 1 - union-find-network-lab benchmark artifacts slice

## Focus
- inspect benchmark-series CLI ergonomics and export-path validation

## Findings
1. `--output-csv` needed a clear guard so users do not request CSV export without benchmark-series mode.

## Fixes applied
- added argument validation that rejects `--output-csv` unless `--benchmark-series` is enabled.
- smoke-tested the failure path to confirm it returns concise `argparse` usage output instead of a traceback.
