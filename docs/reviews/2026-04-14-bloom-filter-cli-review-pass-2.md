# Bloom filter CLI review pass 2 — 2026-04-14

## Focus
CLI smoke review and output contract audit.

## Checks
- Ran the unit test suite.
- Ran the new `benchmark` subcommand manually with a fixed seed.
- Verified output contains both estimated and observed false-positive rates plus counts.

## Findings
- No additional issues found after the streaming insertion fix.
- Output is deterministic enough for tests when a seed is provided.
