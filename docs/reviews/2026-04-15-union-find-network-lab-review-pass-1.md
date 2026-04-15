# Review pass 1 - union-find-network-lab CSV import slice

## Focus
- inspect new CLI modes for argument validation and operator ergonomics

## Findings
1. Invalid combinations such as `--benchmark --script ...` produced raw Python tracebacks instead of user-friendly CLI errors.

## Fixes applied
- wrapped `ValueError` paths through `argparse` so bad inputs now fail with concise usage output and a clear error message.
